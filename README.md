
This is the streamlit app I have created which lets a user request scheduled events and cancel events from their Calendly. The app uses calendly API to fetch all the events.

This application allows users to interact with their Calendly schedule through a conversational interface, enabling them to query and manage their upcoming events.

### Functionality

* **Retrieve Scheduled Events:** Users can ask questions about their upcoming Calendly events, such as "What meetings do I have tomorrow?" or "When is my next appointment with [client name]?".
* **Cancel Events:** Users can request to cancel specific events by providing details like the event name, date, or time.

### Technologies Used

* **Streamlit:**  For building the web application and user interface.
* **Langchain:** A framework for developing applications with LLMs (Large Language Models).
* **ChatOpenAI:** Provides access to OpenAI's GPT-3.5-turbo language model for natural language understanding and generation.
* **Calendly API:** Interacts with the Calendly platform to retrieve and manage event data.
* **Python Libraries:** dotenv, requests, datetime, asyncio

### Installation and Setup

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/calendly_chatbot.git
```
2. **Install dependencies:** 
```bash
pip install -r requirements.txt
```
3. **Set up environment variables:**
   * Create a `.env` file in the project root directory.
   * Add your OpenAI API key and Calendly personal access token to the `.env` file as follows:
   ```
   OPENAI_API_KEY=your_openai_api_key
   PERSONAL_ACCESS_TOKEN=your_calendly_personal_access_token
   ```

4. **Run the application:**
```bash
streamlit run calendly_chatbot.py
```

### Usage

1. **Open the application in your web browser.** The URL will be displayed in the terminal after running the `streamlit run` command.
2. **Start chatting with the bot.** Ask questions about your Calendly schedule or request to cancel events.
3. **The bot will respond based on the information retrieved from the Calendly API.** 

### Example Interactions

### Future Improvements

### Contributing
