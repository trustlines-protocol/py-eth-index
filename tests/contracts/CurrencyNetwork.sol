pragma solidity ^0.4.0;

// This class has to be called CurrencyNetwork, because we need to be compatible with
// logdecode.build_address_to_abi_dict

contract CurrencyNetwork {
  event Transfer(address indexed _from, address indexed _to, uint _value);

  function CurrencyNetwork() public {
  }

  function makeTransfer(address _from, address _to, uint _value) public {
    emit Transfer(_from, _to, _value);
  }
}
