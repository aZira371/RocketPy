from inspect import getsourcelines


class _ControllerPrints:
    """Class that holds prints methods for Controller class.

    Attributes
    ----------
    _ControllerPrint.controller : controller
        Controller object that will be used for the prints.
    """

    def __init__(
        self,
        controller,
    ):
        """Initializes _ControllerPrints class

        Parameters
        ----------
        controller: Controller
            Instance of the Controller class.

        Returns
        -------
        None
        """
        self.controller = controller

    def controller_function(self):
        """Prints the controller function information.

        Returns
        -------
        None
        """
        if self.controller.controller_function.__name__ == "<lambda>":
            line = getsourcelines(self.controller.controller_function)[0][0]
            print("Controller function: " + line.split("=")[0].strip())
        else:
            print(
                "Controller function: " + self.controller.controller_function.__name__
            )
        if self.controller.sampling_rate is None:
            print("Controller refresh rate: continuous")
        else:
            print(f"Controller refresh rate: {self.controller.sampling_rate:.3f} Hz")

    def controlled_objects(self):
        """Prints the objects controlled by the controller."""
        print("Controlled Objects")
        controlled_objects = self.controller.controlled_objects
        if not isinstance(controlled_objects, (list, tuple)):
            controlled_objects = [controlled_objects]
        for obj in controlled_objects:
            print(getattr(obj, "name", str(obj)))

    def all(self):
        """Prints all information about the controller.

        Returns
        -------
        None
        """

        print("\nController Details\n")
        print(self.controller)
        self.controller_function()
        self.controlled_objects()
