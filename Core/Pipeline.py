# distutils: language=c++


class Pipeline:
    pipe_names:list
    _start_management:list
    _url_management:list
    _page_management:list
    _data_management:list
    _end_management:list
    _post_management:list
    _event_management:list
    _route_management:list

    def __init__(self):
        self.pipe_names = [[], [], [], [], [], []]
        self._start_management = []
        self._url_management = []
        self._page_management = []
        self._data_management = []
        self._end_management = []
        self._post_management = []
        self._event_management = []
        self._route_management = []
        setattr(self, "Pipeline_init", True)

    def add_pipe(self, step, function, name=None, *, position=-1):
        if(type(step) is int and 0 <= step <= 4):
            self.pipe_names[step].insert(position, name)
            [
                self._start_management,
                self._url_management, 
                self._page_management, 
                self._data_management,
                self._end_management,
                self._post_management
            ][step].insert(position, function)
        elif(step == "start"):
            self._start_management.insert(position, function)
            self.pipe_names[0].insert(position, name)
        elif(step == "url"):
            self._url_management.insert(position, function)
            self.pipe_names[1].insert(position, name)
        elif(step == "page"):
            self._page_management.insert(position, function)
            self.pipe_names[2].insert(position, name)
        elif(step == "data"):
            self._data_management.insert(position, function)
            self.pipe_names[3].insert(position, name)
        elif(step == "end"):
            self._end_management.insert(position, function)
            self.pipe_names[4].insert(position, name)
        elif(step == "post"):
            self._post_management.insert(position, function)
            self.pipe_names[5].insert(position, name)
        elif(step == "event"):
            self._event_management.insert(position, function)
        elif(step == "routing"):
            self._route_management.insert(position, function)
        else:
            raise ValueError("Invalid step: {}".format(step))