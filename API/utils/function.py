from inspect import iscoroutinefunction


async def argkwarg(num:int, name:str, cls, default_call, args, kwargs, can_be_none=False,):
    print(f"Check var {name}")
    in_kwargs = name in kwargs

    if(num is not None or (num < len(args) or not in_kwargs)):
        if(len(args) <= num):
            args.extend([None] * (num - len(args) + 1))
        
        if(in_kwargs):
            print(f"Kwargs -> args[{num}]")
            arg = args[num] = kwargs.pop(name)
        else:
            arg = args[num]
            if(arg is None):
                if(not can_be_none or default_call is not None):
                    assert default_call is not None, f"{name} must not be None"
                    print(f"Default -> args[{num}]")

                    if(iscoroutinefunction(default_call)):
                        arg = args[num] = await default_call()
                    else:
                        arg = args[num] = default_call()
                else:
                    print(f"None -> args[{num}]")

            elif(cls is not None):
                assert isinstance(arg, cls), f"arg {name} must be a {[c.__name__ for c in cls] if type(cls) == tuple else cls.__name__} instance, but is {arg.__class__.__name__}\nValue: {arg}"
                print(f"Verified args[{num}]")

        return arg
    
    else:
        kwarg = kwargs.get(name, None)
        if(kwarg is None):
            if(not can_be_none or default_call is not None):
                assert default_call is not None, f"{name} must not be None"
                print(f"Default -> kwargs[{name}]")

                if(iscoroutinefunction(default_call)):
                    kwarg = kwargs[name] = await default_call()
                else:
                    kwarg = kwargs[name] = default_call()
            else:
                print(f"None -> args[{num}]")
        elif(cls is not None):
            assert isinstance(kwarg, cls), f"kwarg {name} must be a {[c.__name__ for c in cls] if type(cls) == tuple else cls.__name__} instance, but is {kwarg.__class__.__name__}\nValue: {kwarg}"
            print(f"Verified args[{num}]")

        return kwarg

def sargkwarg(num:int, name:str, cls, default_call, args, kwargs, can_be_none=False):
    print(f"Check var {name}")
    in_kwargs = name in kwargs

    if(num is not None):
        if(len(args) <= num):
            args.extend([None] * (num - len(args) + 1))
        
        if(in_kwargs):
            print(f"Kwargs -> args[{num}]")
            arg = args[num] = kwargs.pop(name)
        else:
            arg = args[num]
            if(arg is None):
                if(not can_be_none or default_call is not None):
                    assert default_call is not None, f"{name} must not be None"
                    print(f"Default -> args[{num}]")

                    arg = args[num] = default_call()
                else:
                    print(f"None -> args[{num}]")
            elif(cls is not None):
                assert isinstance(arg, cls), f"arg {name} must be a {[c.__name__ for c in cls] if type(cls) == tuple else cls.__name__} instance, but is {arg.__class__.__name__}\nValue: {arg}"
                print(f"Verified args[{num}]")

        return arg
    
    else:
        kwarg = kwargs.get(name, None)
        if(kwarg is None):
            if(not can_be_none or default_call is not None):
                assert default_call is not None, f"{name} must not be None"
                print(f"Default -> kwargs[{name}]")

                kwarg = kwargs[name] = default_call()
            else:
                print(f"None -> kwargs[{name}]")
        elif(cls is not None):
            assert isinstance(kwarg, cls), f"kwarg {name} must be a {[c.__name__ for c in cls] if type(cls) == tuple else cls.__name__} instance, but is {kwarg.__class__.__name__}\nValue: {kwarg}"
            print(f"Verified kwargs[{name}]")

        return kwarg


if(__name__ == "__main__"):
    args = []
    kwargs = {}

    sargkwarg(0, 'test', int, lambda : 25, args, kwargs)
    print(args, kwargs)
    