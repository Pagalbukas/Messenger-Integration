# Pagalbukas Messenger integration

This repository contains code for Pagalbukas' Messenger integration which automatically posts
summaries of schedule to a specified Messenger thread.

## How to set up?

To set up, you first need to install at least Python 3.8 and the required packages as defined
inside the `requirements.txt` file.

You will then need to rename `config.py.example` file to `config.py` and replace constants with
credentials and configuration details. Please note that every constant is of a string type.

You will also need to install the PhantomJS web driver available [here](https://phantomjs.org/).

You will also need a `session.json` file for connecting to Messenger which can be obtained by the
following snippet:

```python
import fbchat
import json

session = fbchat.Session.login("email", "password", on_2fa_callback=lambda: input("2FA Code: "))
with open("session.json", "w") as f:
    json.dump(session.get_cookies(), f)
```
