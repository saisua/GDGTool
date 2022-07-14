from regex import A


def argkwarg(num:int, name:str, cls, default_call, *args, can_be_none=False, **kwargs):
    if(num is not None and len(args) > num):
        arg = args[num]
        if(arg is None):
            if(not can_be_none or default_call is not None):
                assert default_call is not None, f"{name} must not be None"

                arg = args[num] = default_call()
        elif(cls is not None):
            assert isinstance(arg, cls), f"arg {name} must be a {cls.__name__} instance, but is {arg.__class__.__name__}"

        return arg
    
    else:
        kwarg = kwargs.get(name, None)
        if(kwarg is None):
            if(not can_be_none or default_call is not None):
                assert default_call is not None, f"{name} must not be None"

                kwarg = kwargs[name] = default_call()
        elif(cls is not None):
            assert isinstance(kwarg, cls), f"kwarg {name} must be a {cls.__name__} instance, but is {arg.__class__.__name__}"

        return kwarg