from sploitkit import Module, Config, Option, Command
from dotenv import load_dotenv
import os
from theblockchainapi import BlockchainAPIResource, Blockchain, BlockchainNetwork, Wallet

class ethereumWalletBalance(Module):
    """ This module find Wallet Balance
    Author:  laet4x
    Version: 1.0
    """

    load_dotenv()
    BLOCKCHAIN = Blockchain.ETHEREUM
    NETWORK = BlockchainNetwork.EthereumNetwork.MAINNET
    UNIT = 'ether'    
    BLOCKCHAIN_API_KEY_ID = os.getenv('BLOCKCHAIN_API_KEY_ID')
    BLOCKCHAIN_API_SECRET_KEY = os.getenv('BLOCKCHAIN_API_SECRET_KEY')
    BLOCKCHAIN_API_RESOURCE = BlockchainAPIResource(
        api_key_id=BLOCKCHAIN_API_KEY_ID,
        api_secret_key=BLOCKCHAIN_API_SECRET_KEY,
        blockchain=BLOCKCHAIN,
        network=NETWORK
    )     

    config = Config({
        Option(
            'ADDRESS',
            "Provide your target address",
            True,
        ): str("0xbFCC250e1d5603d144c7ce99834403B0452d2644"),
    })

    def prerun(self):
        if(self.BLOCKCHAIN_API_KEY_ID == "" and self.BLOCKCHAIN_API_SECRET_KEY == ""):
            print("Error: .env BLOCKCHAIN_API_KEY_ID and BLOCKCHAIN_API_SECRET_KEY are empty")
            raise Exception("Fill in your key ID pair!")
     
    def run(self):
        address = self.config.option('ADDRESS').value
        result = self.BLOCKCHAIN_API_RESOURCE.get_balance(address, unit=self.UNIT)
        print(f"Balance of {address}")
        print(result)
        # wallet = Wallet(address)
        # addr = wallet.get_address(address)
        # print(addr.balance)



