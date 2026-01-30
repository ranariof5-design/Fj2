"""
Sorting algorithms for expense tracker
- Date: Normal array sorting
- Name: Binary Search Tree (BST)
- Price: Max Heap
"""

class BSTNode:
    """Binary Search Tree Node for name sorting"""
    def __init__(self, expense):
        self.expense = expense
        self.left = None
        self.right = None

class BST:
    """Binary Search Tree for sorting expenses by name"""
    def __init__(self):
        self.root = None
    
    def insert(self, expense):
        """Insert expense into BST"""
        if not self.root:
            self.root = BSTNode(expense)
        else:
            self._insert_recursive(self.root, expense)
    
    def _insert_recursive(self, node, expense):
        """Recursively insert expense"""
        # Compare names (case-insensitive)
        if expense['name'].lower() < node.expense['name'].lower():
            if node.left is None:
                node.left = BSTNode(expense)
            else:
                self._insert_recursive(node.left, expense)
        else:
            if node.right is None:
                node.right = BSTNode(expense)
            else:
                self._insert_recursive(node.right, expense)
    
    def inorder_traversal(self):
        """Return sorted list of expenses (in-order traversal)"""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        """Recursively traverse in-order"""
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.expense)
            self._inorder_recursive(node.right, result)

def sort_by_name_bst(expenses):
    """Sort expenses by name using BST"""
    if not expenses:
        return []
    
    bst = BST()
    for exp in expenses:
        bst.insert(exp)
    
    return bst.inorder_traversal()


class MaxHeap:
    """Max Heap for sorting expenses by price (descending)"""
    def __init__(self):
        self.heap = []
    
    def insert(self, expense):
        """Insert expense into max heap"""
        self.heap.append(expense)
        self._heapify_up(len(self.heap) - 1)
    
    def _heapify_up(self, index):
        """Move element up to maintain heap property"""
        if index == 0:
            return
        
        parent_index = (index - 1) // 2
        if self.heap[index]['amount'] > self.heap[parent_index]['amount']:
            self.heap[index], self.heap[parent_index] = self.heap[parent_index], self.heap[index]
            self._heapify_up(parent_index)
    
    def extract_max(self):
        """Remove and return expense with maximum amount"""
        if not self.heap:
            return None
        
        if len(self.heap) == 1:
            return self.heap.pop()
        
        max_expense = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        
        return max_expense
    
    def _heapify_down(self, index):
        """Move element down to maintain heap property"""
        largest = index
        left = 2 * index + 1
        right = 2 * index + 2
        
        if left < len(self.heap) and self.heap[left]['amount'] > self.heap[largest]['amount']:
            largest = left
        
        if right < len(self.heap) and self.heap[right]['amount'] > self.heap[largest]['amount']:
            largest = right
        
        if largest != index:
            self.heap[index], self.heap[largest] = self.heap[largest], self.heap[index]
            self._heapify_down(largest)
    
    def get_sorted(self):
        """Return all expenses sorted by amount (descending)"""
        result = []
        while self.heap:
            result.append(self.extract_max())
        return result

def sort_by_price_heap(expenses):
    """Sort expenses by price using Max Heap (highest first)"""
    if not expenses:
        return []
    
    heap = MaxHeap()
    for exp in expenses:
        heap.insert(exp)
    
    return heap.get_sorted()


def sort_by_date_array(expenses, reverse=False):
    """Sort expenses by date using normal array sorting"""
    if not expenses:
        return []
    
    # Use Python's built-in sort (Timsort - hybrid of merge sort and insertion sort)
    sorted_expenses = sorted(expenses, key=lambda x: x['date'], reverse=reverse)
    return sorted_expenses


def sort_by_category(expenses):
    """Sort expenses by category (alphabetically)"""
    if not expenses:
        return []
    
    return sorted(expenses, key=lambda x: x['category'].lower())


def search_expenses(expenses, query):
    """
    Search expenses by name, category, or amount
    Returns list of matching expenses
    """
    if not query or not expenses:
        return expenses
    
    query = query.lower().strip()
    results = []
    
    for exp in expenses:
        # Search in name
        if query in exp['name'].lower():
            results.append(exp)
            continue
        
        # Search in category
        if query in exp['category'].lower():
            results.append(exp)
            continue
        
        # Search in amount (as string)
        try:
            if query in str(exp['amount']):
                results.append(exp)
                continue
        except:
            pass
        
        # Search in date
        if query in exp['date']:
            results.append(exp)
            continue
    
    return results