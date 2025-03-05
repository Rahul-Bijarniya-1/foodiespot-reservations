# FoodieSpot Restaurant Reservation System

A simple LLM-powered restaurant reservation assistant that helps users find restaurants and make reservations through natural language.

## Features

- **Restaurant Search**: Search for restaurants by cuisine, location, and price range
- **Availability Checking**: Check available time slots for a specific date
- **Reservation Management**: Make, view, and cancel reservations
- **Natural Language Interface**: Interact with the system through natural language

## Getting Started

### Prerequisites

- Python 3.8 or higher
- API key for a LLM provider (like Llama 3.1-8b)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/foodiespot.git
   cd foodiespot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API key:
   ```bash
   cp .env.example .env
   # Edit .env with your actual API key
   ```

### Running the Application

Start the Streamlit app:
```bash
streamlit run app.py
```

The application will be available at http://localhost:8501

## Project Structure

- `app.py`: Main Streamlit application
- `models/`: Data models for restaurants and reservations
- `data/`: Data storage and sample data generation
- `tools/`: Core functionality for searching, checking availability, and making reservations
- `utils/`: Utility functions for LLM integration and formatting

## How It Works

1. The user interacts with the Streamlit chat interface
2. User messages are sent to the LLM with tool definitions
3. The LLM generates responses and decides when to call tools
4. Tool results are incorporated into the final response
5. All data is stored in simple JSON files

## Customization

- Modify `data/sample_data.py` to change the sample restaurant data
- Add new tools in the `tools/` directory and register them in `app.py`
- Customize the system prompt in `app.py` to change the assistant's behavior

## License

This project is licensed under the MIT License - see the LICENSE file for details.