from collections import deque
from typing import *

class __Any:
	def __instancecheck__(self, instance):
		return True

def deep_search(data: Dict[str, Any], /, key_search: str=None, type_search: Type=Any) -> List[Any]:
	stack = deque([data])
	results = []
	
	while stack:
		current = stack.pop()
		
		if (type_search is Any or isinstance(current, type_search)) and (key_search is None or not hasattr(current, '__iter__') or key_search in current):
			results.append(current)
		

		if isinstance(current, dict):
			stack.extend(current.values())
		elif isinstance(current, list):
			stack.extend(current)
	
	return results