from collections import defaultdict


class ConfidenceEngine:

    def __init__(self):

        # Persist collision history
        self.event_history = defaultdict(int)
        self.emitted_events = set()

        # Frames required to confirm
        self.confirmation_threshold = 2

    def update(self, collision_events):

        confirmed_events = []

        active_keys = set()

        for event in collision_events:

            v1 = event["vehicle_1"]
            v2 = event["vehicle_2"]

            key = tuple(sorted([v1, v2]))

            if key in self.emitted_events:
                continue

            active_keys.add(key)

            self.event_history[key] += 1

            # Confirm only after persistence
            if (
                self.event_history[key]
                >= self.confirmation_threshold
            ):

                event["confirmed"] = True
                self.emitted_events.add(key)

                confirmed_events.append(event)

        # Decay inactive events
        keys_to_remove = []

        for key in self.event_history:

            if key not in active_keys:

                self.event_history[key] -= 1

                if self.event_history[key] <= 0:
                    keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.event_history[key]

        return confirmed_events
