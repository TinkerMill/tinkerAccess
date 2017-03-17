#Integration Testing

These test use a custom [VirtualDevice](utils/VirtualDevice.py) fixture which replaces the GPIO library at runtime, so the pin state is stored in memory.   

The advantage of this is the test can be written and run in an environment where GPIO won't load 
(i.e. the build server of a development pc)


Example:

```
    def test_login(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            opts = get_default_opts(temp_dir)
            with patch.object(requests, 'get') as mock_get, VirtualDevice(opts) as device:

                expected_transitions = [
                    State.INITIALIZED,
                    State.IDLE
                ]  

                # Assert that the device has initialized and is idle
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)  

                # Assert that a valid login causes the device to transition to in_use and enables the expected pins.
                mock_get.return_value = valid_login_response
                device.scan_badge('some_badge_code')
                expected_transitions.append(State.IN_USE)
                self.assertTransitions(device, expected_transitions)
                self.assertInUsePins(opts, device)

```