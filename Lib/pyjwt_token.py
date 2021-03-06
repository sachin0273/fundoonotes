"""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Purpose: in this module we create jwt_token for email verification 
author:  Sachin Shrikant Jadhav
since :  25-09-2019

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

"""
import pdb

import jwt
import requests
from Fundoo.settings import base


class Jwt:
    def register_token(self, payload):
        """
        :param payload: here we passing user information
        :return:this function return jwt token
        """
        try:
            jwt_token = {'token': jwt.encode(payload, "SECRET_KEY", algorithm="HS256").decode('utf-8')}
            return jwt_token['token']
        except Exception:
            return False

    def login_token(self, payload):
        try:
            pdb.set_trace()
            response = requests.post(base.Token, payload)
            return response.json()['access']
        except Exception:
            return False
