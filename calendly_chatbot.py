import os
import datetime
import requests
import os
# from dotenv import load_dotenv
import json
from datetime import datetime
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import streamlit as st
from streamlit_chat import message
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.prompts.prompt import PromptTemplate
import requests
import asyncio

# load_dotenv()


# os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Define conversation prompt template
template = """Analyze the list of scheduled events from calendly info and answer the user's question.
You can access calendly data from the streamlit session state variable 'calendly_info'.
If the AI does not know the answer to a question, it truthfully says it does not know and only answer from the list of events. 
Only answer questions related to calendly events.

Current conversation:
{history}
{input}
calendlly:
"""
prompt_template = PromptTemplate(
    input_variables=["history", "input"], template=template
)

llm = ChatOpenAI(model="gpt-3.5-turbo-0125")


@tool
def scheduled_events():
    """Provides the list of scheduled events"""


@tool
def cancel_event(event_id):
    """ "cancels an event, deletes and event, removes an event"""


tools = [cancel_event, scheduled_events]

llm_with_tools = llm.bind_tools(tools)

# PERSONAL_ACCESS_TOKEN = os.environ.get("PERSONAL_ACCESS_TOKEN")
PERSONAL_ACCESS_TOKEN = st.secrets["PERSONAL_ACCESS_TOKEN"]
headers = {
    "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

st.session_state.calendly_info = None


def get_org_id():
    response = requests.get("https://api.calendly.com/users/me", headers=headers)

    if response.status_code == 200:
        user_info = response.json()
        org_id = user_info["resource"]["current_organization"]
        return org_id
    else:
        print(f"Error: {response.status_code}")


async def get_scheduled_events():
    organization_url = get_org_id()
    response = requests.get(
        f"https://api.calendly.com/scheduled_events?organization={organization_url}",
        headers=headers,
    )
    if response.status_code == 200:
        events = response.json()
        filtered_events = await extract_event_info(events)
        # print(filtered_events)
        return filtered_events
    else:
        print(f"Error: {response.status_code}")


async def cancel_event(event_id):
    organization_url = get_org_id()
    response = requests.post(
        f"https://api.calendly.com/scheduled_events/{event_id}/cancellation?organization={organization_url}",
        headers=headers,
    )
    if response.status_code == 200:
        return {"message": "Event cancelled successfully"}
    else:
        print(f"Error: {response.status_code}")


async def extract_event_info(events):
    event_info = []
    for event in events["collection"]:
        if event["status"] == "active":
            time = await parse_start_time(event["start_time"])
            event_info.append(
                {
                    "name": event["name"],
                    "event_date": time["full_date"],
                    "event_time": time["time"],
                    "event_day": time["day_of_week"],
                    "event_month": time["month"],
                    "uuid": event["uri"].split("/")[-1],
                    "status": event["status"],
                }
            )
    return event_info


async def call_function(func_output):
    if func_output[0]["name"] == "scheduled_events":
        events = await get_scheduled_events()
        return events
    elif func_output[0]["name"] == "cancel_event":
        #   cancel_event()
        pass


async def parse_start_time(start_time):
    """Parse the start time of a calendly event into its components"""
    # convert the star_time to current timezone
    # start_time = start_time.astimezone(timezone('US/Pacific'))
    # Split the input start_time on 'T' to separate date from time
    date_part, time_part = start_time.split("T")
    timestamp = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    # Extract the day, month, and year
    day = timestamp.day
    month = timestamp.month
    year = timestamp.year

    hour = timestamp.hour
    minute = timestamp.minute

    day_of_week = timestamp.strftime("%A")
    month_name = timestamp.strftime("%B")

    # Prepare the output with all relevant time details
    return {
        "full_date": date_part,
        "time": f"{hour}:{minute}",  # format hour and minute to a simple time string
        "hour": hour,
        "minute": minute,
        "day_of_week": day_of_week,
        "month": month_name,
        "day": day,
        "month": month,
        "year": year,  # year as a string if needed for consistency
    }


async def chat_with_calendly():
    memory_length = 3
    if "chat_memory" not in st.session_state:
        st.session_state.chat_memory = ConversationBufferWindowMemory(
            k=1, return_messages=True
        )
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "calendly", "content": "How can I help you today?"}
        ]

    # llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
    conversation = ConversationChain(
        memory=st.session_state.chat_memory,
        llm=llm
        # verbose=True,
        # prompt=prompt_template,
    )
    if st.session_state.messages[-1]["role"] != "user":
        if query := st.chat_input("Your question"):
            st.session_state.messages.append({"role": "user", "content": query})
            func_output = llm_with_tools.invoke(query).tool_calls
            # intialized the calendly_info variable
            calendly_info = None
            print(type(calendly_info))
            calendly_info = await call_function(func_output)
            # convert the calendly_info json data to string withoud json.dumps
            print(type(calendly_info))
            print(calendly_info)
            calendly_info = str(calendly_info)
            # store the calendly info in the session state
            st.session_state.calendly_info = calendly_info

    for message in st.session_state.messages:  # Display the prior chat messages
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is not from calendly, generate a new response
    if st.session_state.messages[-1]["role"] != "calendly":
        with st.chat_message("calendly"):
            with st.spinner("Thinking..."):
                prompt = (
                    query
                    + " answer looking at the data "
                    + calendly_info
                )
                response = conversation.predict(input=prompt)
                st.write(response)
                message = {"role": "calendly", "content": response}
                st.session_state.messages.append(
                    message
                )  # Add response to message history


async def process_query(query):
    func_output = llm_with_tools.invoke(query).tool_calls
    if func_output[0]["name"] == "scheduled_events":
        events = await get_scheduled_events()
        print(events)
        return events
    elif func_output[0]["name"] == "cancel_event":
        await cancel_event()


async def chat_with_calendlyio():
    await chat_with_calendly()


# Example usage
if __name__ == "__main__":
    # query = "Are there any events for me tomorrow?"
    # asyncio.run(process_query(query))

    # print(parse_start_time("2024-04-25T13:00:00.000000Z"))

    asyncio.run(chat_with_calendlyio())
