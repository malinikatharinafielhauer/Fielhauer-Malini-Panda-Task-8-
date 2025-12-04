# Part 8 — Starter

This part builds on your Part 7 solution. The key goal is to move functionality from app.py into the classes. See ToDos for details.

## Run the app

```bash
python -m part8.app
```

## What to implement (ToDos)

As always, your todos are located in `app.py`, specifically, in `part8/app.py`

0. **Copy** your implementation from part 7. Use ``LineMatch``, ``SearchResult``, ``Sonnet``, and ``Configuration`` and access their attributes using dot notation.
1. Move the ``combine_results`` function to the ``SearchResult`` class and rename it to ``combine_with``. The first parameter ``result1`` should be renamed to ``self`` to adhere to Python's naming conventions. You could (and should) rename the second parameter also, e.g., to ``other``. You will need to change the calls to ``combine_results(combined_result, result)`` to ``combined_result.combine_with(result)``. 
2. Move the printing of one ``SearchResult`` (lines 139 to 151 in the Starter's ``app.py``) to a method ``print`` in class ``SearchResult``. You will need to pass ``idx`` and ``highlight`` to the ``print`` method. Also, ``ansi_highlight`` needs to be moved alongside ``print`` to be available in ``SearchResult``. You then should be able to call it using ``r.print(idx, highlight)`` in ``print_results``.
3. Move the ``search_sonnet`` function to the ``Sonnet`` class and rename it to ``search_for``. The first parameters should be renamed to ``self`` following Python's naming conventions. For this to work you will need to move ``find_spans`` to ``Sonnet`` also.
