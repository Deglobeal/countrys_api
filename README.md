# Country Currency & Exchange API

A FastAPI-based RESTful API that fetches country data and exchange rates, stores them in MySQL, and provides CRUD operations.

## Features

- Fetch country data from REST Countries API
- Get exchange rates from Open Exchange Rates API
- Compute estimated GDP based on population and exchange rates
- CRUD operations for country data
- Filtering and sorting capabilities
- Summary image generation
- MySQL database integration

## Setup Instructions

### Prerequisites

- Python 3.8+
- MySQL Server
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd country-api