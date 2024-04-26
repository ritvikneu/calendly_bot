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
import pytz
import tzlocal
import re
# from langchain.tooling import Tool

# load_dotenv()


# os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Define conversation prompt template
template = """Analyze the list of scheduled events from calendly info and answer the user's question.
You can access calendly data from the streamlit session state variable 'calendly_info'.
You are capable of listing the scheduled events by calling the 'scheduled_events' tool and cancel the events by calling the 'cancel_event' tool.
Only answer questions related to calendly events.

Current conversation:
{history}
{input}
calendlly:
"""
prompt_template = PromptTemplate(
    input_variables=["history", "input"], template=template
)



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


async def cancel_event_with_id(event_id):
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
            time = await parse_start_time_local(event["start_time"])
            # append only if the event is present or future
            if time["full_date"] >= datetime.now().strftime("%Y-%m-%d"):
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

# class ScheduledEvents(Tool):
#     def run(self):
#         return "List of scheduled events"

# class CancelEvents(Tool):
#     def run(self, event_id):
#         return f"Event {event_id} cancelled"

@tool
def scheduled_events():
    """Provides the list of scheduled events"""
    pass
@tool
def cancel_events():
    """To cancel an event or remove an event or cancel a meeting"""
    pass

tools = [cancel_events, scheduled_events]
llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
llm_with_tools = llm.bind_tools(tools)


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
        llm=llm,
        verbose=True,
        prompt=prompt_template,
    )

    calendly_info = None
    func_event = None
    calendly_info = await get_scheduled_events()
    calendly_info = str(calendly_info)

    if st.session_state.messages[-1]["role"] != "user":
        if query := st.chat_input("Your question"):
            st.session_state.messages.append({"role": "user", "content": query})
            try:
                # print("Query:----------------", query)
                invoke_tool = llm_with_tools.invoke(query).tool_calls
                invoke_tool_event = invoke_tool[0]["name"]
                # tool_calls = llm_with_tools.invoke(query).tool_calls
                # print("tool_calls:----------------", tool_calls[0]["name"])
                # print("func_event:----------------", func_event)
                # intialized the calendly_info variable
            except Exception as e:
                print(e)
                st.write("Failed to process the query.")
            st.session_state.calendly_info = calendly_info

    for message in st.session_state.messages:  # Display the prior chat messages
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is not from calendly, generate a new response
    if st.session_state.messages[-1]["role"] != "calendly":
        with st.chat_message("calendly"):
            with st.spinner("Thinking..."):
                if invoke_tool_event == "scheduled_events":
                    prompt = (
                        query
                        + " answer looking at the data" + calendly_info
                    )
                
                    response = conversation.predict(input=prompt)
                    st.write("-",response)
                    message = {"role": "calendly", "content": response}
                    st.session_state.messages.append(
                        message
                    )  
                elif invoke_tool_event == "cancel_events":
                    # Compose the prompt to ask the AI to return only the UUID of the event to cancel.
                    prompt = query + " .Only return the uuid of the event to cancel from json data" + calendly_info
                    # print("Prompt:------", prompt)
                    response = llm.invoke(prompt)
                    uuid = await extract_uuid(response.content)
                    # st.write("uuid",uuid)
                    response = cancel_event_with_id(uuid)
                    st.write(":",response)

# Cancel the event on Friday
async def extract_uuid(response_content):
    # UUIDs are typically in the format of 8-4-4-4-12 hexadecimal digits
    uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    try:
        # Search for the UUID pattern in the response content
        match = re.search(uuid_pattern, response_content, re.IGNORECASE)
        if match:
            uuid = match.group(0)
            print("Extracted UUID:", uuid)
            return uuid
        else:
            print("No UUID found in the response.")
            return None
    except Exception as e:
        print("Error extracting UUID:", str(e))
        return None
  
async def parse_start_time_local(start_time):
    # Parse the UTC time from the ISO 8601 string
    utc_timestamp = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    utc_timestamp = utc_timestamp.replace(tzinfo=pytz.utc)
    
    # Get local timezone
    local_timezone = tzlocal.get_localzone()

    # Convert UTC to local time
    local_timestamp = utc_timestamp.astimezone(local_timezone)

    # Extract the day, month, and year
    day = local_timestamp.day
    month = local_timestamp.month
    year = local_timestamp.year

    # Extract hour and minute
    hour = local_timestamp.hour
    minute = local_timestamp.minute

    # Extract the day of the week and month name
    day_of_week = local_timestamp.strftime("%A")
    month_name = local_timestamp.strftime("%B")

    # Format date part
    date_part = local_timestamp.strftime("%Y-%m-%d")

    # Prepare the output with all relevant time details
    return {
        "full_date": date_part,
        "time": f"{hour:02}:{minute:02}",  # format hour and minute to a simple time string
        "hour": hour,
        "minute": minute,
        "day_of_week": day_of_week,
        "month": month_name,
        "day": day,
        "year": year
    }



async def chat_with_calendlyio():
    await chat_with_calendly()


# Example usage
if __name__ == "__main__":
    # query = "Please cancel the event on Tuesday"
    # asyncio.run(process_query(query))

    # print(parse_start_time("2024-04-25T13:00:00.000000Z"))

    asyncio.run(chat_with_calendlyio())
