# Friedjof Noweck
# 18.08.2021 Mi

from server.backend.utils.orMapper import *
from server.backend.utils.frequentlyUsedQueries import FrequentlyUsedQueries as FUQ


# Example for FUQ's
if __name__ == "__main__":
    fuq = FUQ()
    print(f"User: {fuq.get_user_by(token_id='78619889fd6e4af38c543d2e5d7acb9e').get().Nickname}")
    print(f"User: {fuq.get_user_by(login_id='1').get().Nickname}")
    print(f"Token: {fuq.get_token_by(user_id='719b147bed674b17ae4eee5f57ec2d65').get().TOTP}")
    # [...]
