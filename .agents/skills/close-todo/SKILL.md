---
name: close-todo
description: find and close todo tasks
---
# Instructions
1. find in code `#TODO:`
```example of todo
#TODO: add method sum a + b
```
2. take first TODO
3. read task in todo
4. make implementation plan. 
  DON'T forget skills:
    - [documentation](skill:documentation)
    - [code-coverage](skill:code-coverage)
    - [implementition-plan-metadata](skill:implementition-plan-metadata)
5. assert does git diff is empty 
6. approve implementation plan with user and in case git diff is not empty ask user clean git diff
7. apply implementaiton plan
8. remove `#TODO: ...` comment
9. add git commit with message `AI close TODO: {text from}`