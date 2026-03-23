# ML Application Developer Take Home Exam
Hello! Thanks so much for applying as an ML Application Developer, and congratulations on making it to the take home exam round.

The task in this exam is to build a low-latency process (<300ms) that will take in RestAPI requests for giving a price for a product, communicate with external services, and return the price based on the result of the calls.

## Setup
You can use any python version 3.12 and above. You can use (uv)[https://docs.astral.sh/uv/] for package and project management.  

This assignment requires you to run multiple applications locally (both the one you'll create and the ones under `mock_api/`). The application you create must be the one sending the requests to the other mock applications.

## The Task
- Create a Python Application which will:
    1. Accept requests as defined in `shared/schemas/request.py::PricerRequest`. This request will contain the partner id, member id, and product id for which the member is getting the price for
    2. Post to the member data API (`mock_api/member_data.py`) to get that member's data. You can find the request for that API at `shared/schemas/request.py::MemberDataRequest` and the response at `shared/schemas/response.py::MemberDataResponse`. The `last_purchase_datetime` and `last_login_datetime` fields of the response should assumed to be in UTC timezone
    3. Post to the product info API (`mock_api/product_info.py`) to get information on that product You can find the request for that API at `shared/schemas/request.py::ProductInfoRequest` and the response at `shared/schemas/response.py::ProductInfoResponse`
    4. Create the member features that will be sent to the machine learning endpoint, which are:
        - min_price: The minimum price of the product acquired from the product info API
        - default_price: The default price of the product acquired from the product info API
        - max_price: The maximum price of the product acquired from the product info API
        - product_id: Id of the product from the PricerRequest
        - days_since_last_login: Number of days since the last login the member made.
        - days_since_last_transaction: Number of days since the last transaction the member made.
        - avg_transaction_size: `total_transaction_amount` / `number_of_transactions`
        - last_transaction_ratio: `last_transaction_amount` / `avg_transaction_size`
    5. Post those features to the machine learning endpoint (`mock_api/pricing_ml_model.py`) to get the price
    6. Post the auditing information, which are the fields in `shared/schemas/request.py::AuditLogRequest` to the audit API (`mock_api/audit_log.py`)
    7. Return the price given by machine learning endpoint
- Create a CI/CD process that will:
  - Run the tests you have written
  - Lint and type check the code

## What We're Looking For:
- Processing speed/parallelism/latency
- Design patterns/programming paradigm
- Error handling
- Scalability
- High availability
- Documentation
- Clean code
- Stress and unit testing
- Readability
- Logging
- CI/CD
