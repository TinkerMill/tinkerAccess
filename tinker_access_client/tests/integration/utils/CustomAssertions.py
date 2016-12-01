import time
from tinker_access_client.tinker_access_client.ClientOption import ClientOption


# noinspection PyPep8Naming,PyMethodMayBeStatic
class CustomAssertions(object):

    def assertIdlePins(self, opts, device):
        self.assertPins(device, [
            (opts.get(ClientOption.PIN_POWER_RELAY), False),
            (opts.get(ClientOption.PIN_LED_RED), False),
            (opts.get(ClientOption.PIN_LED_GREEN), False),
            (opts.get(ClientOption.PIN_LED_BLUE), True),
        ])

    def assertInUsePins(self, opts, device):
        self.assertPins(device, [
            (opts.get(ClientOption.PIN_POWER_RELAY), True),
            (opts.get(ClientOption.PIN_LED_RED), False),
            (opts.get(ClientOption.PIN_LED_GREEN), True),
            (opts.get(ClientOption.PIN_LED_BLUE), False),
        ])

    def assertPins(self, device, pins=None):
        pins = pins if pins is not None else []

        for (pin, expected_pin_value) in pins:
            actual_pin_value = device.read_pin(pin)
            if expected_pin_value != actual_pin_value:
                raise AssertionError(
                    'Actual pin value:\'{0}\' are not equal to expected pin value \'{1}\''
                    .format(actual_pin_value, expected_pin_value)
                )

    def assertTransitions(self, device, transitions=None, max_wait_time=5):
        transitions = transitions if transitions is not None else []

        current = time.time()
        while transitions != device.transitions() and time.time() - current < max_wait_time:
            time.sleep(0.5)

        # This fixed wait ensures that no other events have trigger additional unexpected transitions
        time.sleep(5)
        if transitions != device.transitions():
            raise AssertionError(
                'Actual transitions:\'{0}\' are not equal to expected transitions \'{1}\''
                .format(device.transitions(), transitions)
            )