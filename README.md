# Part 8 — Starter

This part builds on your Part 7 solution. The key goal is to move functionality from app.py into the classes. See ToDos for details.

Your code should run after you finished a ToDo. You can then make a commit for each individual ToDo. These small commits are called **atomic commits**. Give it a try!

> An **atomic commit** is a version-control concept (most often discussed with Git) where a single commit does exactly one logical change — no more, no less — and is self-contained, consistent, and reversible.

## Run the app

```bash
python -m part8.app
```

## What to implement (ToDos)

As always, your todos are located in `app.py`, specifically, in `part8/app.py`

0. **Copy** your implementation from part 7. Use ``LineMatch``, ``SearchResult``, ``Sonnet``, and ``Configuration`` and access their attributes using dot notation.
1. Move the ``combine_results`` function to the ``SearchResult`` class and rename it to ``combine_with``. The first parameter ``result1`` should be renamed to ``self`` to adhere to Python's naming conventions. You could (and should) rename the second parameter also, e.g., to ``other``. You will need to change the calls to ``combine_results(combined_result, result)`` to ``combined_result.combine_with(result)``. 
2. Move the printing of one ``SearchResult`` (lines 139 to 151 in the Starter's ``app.py``) to a method ``print`` in class ``SearchResult``.

    You will need to pass ``idx``, ``highlight``, and ``total_docs`` to the ``print`` method. 

    Also, ``ansi_highlight`` needs to be moved alongside ``print`` to be available in ``SearchResult`` (see _Coding Hints_ at the end). You then should be able to call it using ``r.print(idx, highlight)`` in ``print_results``.
3. Move the ``search_sonnet`` function to the ``Sonnet`` class and rename it to ``search_for``. The first parameters should be renamed to ``self`` following Python's naming conventions. 

    For this to work you will need to move ``find_spans`` to ``Sonnet`` also (again: see _Coding Hints_)

## Coding Hints

### Type hints in classes
When using the classname as a type hint in a class method, e.g., in 

```python
def combine_with(self, other: SearchResult) -> SearchResult:
    ... code ...
```

PyCharm will complain because it does not yet know the class ``SearchResult``. This is because at that point in the code you are in the process of defining it.

There are two ways to deal with this:
1. Use strings as class names, e.g., 

    ```python
    def combine_with(self, other: "SearchResult") -> "SearchResult":
        ... code ...
    ```
2. or add this import at the beginning of your file: 
 
    ```Python 
    from __future__ import annotations
    ```

Now all your annotations are stored as strings and evaluated later. This is called _Postponed Evaluation of Annotations (PEP 563)_

### Static methods

When moving helper methods to classes, that do not need the object instance to work, e.g., ``find_spans`` you can use a so-called **decorator** to express that fact.

Here is how ``find_spans`` will look like with the decorator:

```python
@staticmethod
def find_spans(text: str, pattern: str):
    """Return [(start, end), ...] for all (possibly overlapping) matches.
    Inputs should already be lowercased by the caller."""
    spans = []
    if not pattern:
        return spans

    for i in range(len(text) - len(pattern) + 1):
        if text[i:i + len(pattern)] == pattern:
            spans.append((i, i + len(pattern)))
    return spans
```

You then can call that function using the class name, e.g.,  ``Sonnet.find_spans(...)``.

