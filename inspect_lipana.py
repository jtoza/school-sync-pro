import lipana
import inspect
from lipana.resources.transactions import Transactions

print("Transactions class help:")
help(Transactions)

print("\nTransactions class source:")
try:
    print(inspect.getsource(Transactions))
except Exception as e:
    print(f"Could not get source: {e}")
