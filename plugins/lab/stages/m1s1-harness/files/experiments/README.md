# The experiments

Three runs of the same thing. The only difference between them is **which tools the model
is given** — the `--tools` flag on the command line.

```
python3 experiments/exp.py 1      no tools at all
python3 experiments/exp.py 2      one tool:  Read
python3 experiments/exp.py 3      two tools: Read and Write
```

The script prints the command before running it. You do not have to use the script — copy
the command, run it yourself, change the prompt. The prompts are plain text files in this
folder, so you can edit them.

After each run, open **`.claude/lab-trace.log`** and look at the last line of the block. It
counts how many times the model was called, and how many tools it asked for.

That number is the thing to watch.

## Why a separate command instead of a slash command

These run as their own `claude` session so that the tool restriction applies only to the
experiment. Your tutor session keeps all of its tools and carries on working — otherwise
switching tools off would switch off the tutor too.
