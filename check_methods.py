import lipana
from lipana.resources.transactions import Transactions

print("Transactions methods:")
print([method for method in dir(Transactions) if not method.startswith('_')])
