# from cosmos_reasoner import CosmosReasoner


# class LocalKinematicVerifier:

#     """
#     Advanced second-stage kinematic verifier.
#     """

#     def __init__(
#         self,
#         confirmation_threshold=84
#     ):

#         self.confirmation_threshold = (
#             confirmation_threshold
#         )

#     def verify(
#         self,
#         event,
#         frame=None
#     ):

#         features = event.get(
#             "candidate_features",
#             {}
#         )

#         # Reject dense traffic flow
#         if features.get(
#             "parallel_side_by_side"
#         ):

#             return self.reject(
#                 event,
#                 "parallel traffic flow"
#             )

#         score = event.get(
#             "collision_score",
#             0
#         )

#         # Spatial evidence
#         if features.get("near_enough"):
#             score += 6

#         if features.get("approaching"):
#             score += 10

#         if features.get("closing_now"):
#             score += 6

#         # Strong impact evidence
#         if features.get(
#             "hard_deceleration"
#         ):
#             score += 16

#         if features.get(
#             "speed_collapse"
#         ):
#             score += 18

#         if features.get(
#             "direction_change"
#         ):
#             score += 14

#         if features.get(
#             "sudden_stop"
#         ):
#             score += 14

#         # Low-speed impact evidence
#         if features.get(
#             "micro_impact"
#         ):
#             score += 16

#         if features.get(
#             "post_impact_pause"
#         ):
#             score += 12

#         if features.get(
#             "rebound_separation"
#         ):
#             score += 14

#         # Heavy suppression
#         if features.get(
#             "parallel_side_by_side"
#         ):
#             score -= 70

#         impact_evidence = any([

#             features.get(
#                 "hard_deceleration"
#             ),

#             features.get(
#                 "speed_collapse"
#             ),

#             features.get(
#                 "direction_change"
#             ),

#             features.get(
#                 "micro_impact"
#             ),

#             features.get(
#                 "post_impact_pause"
#             ),

#             features.get(
#                 "rebound_separation"
#             )
#         ])

#         spatial_evidence = (
#             features.get("near_enough")
#             and
#             (
#                 features.get("approaching")
#                 or
#                 features.get("closing_now")
#             )
#         )

#         verified = (
#             score >= self.confirmation_threshold
#             and
#             impact_evidence
#             and
#             spatial_evidence
#         )

#         if verified:

#             return self.accept(
#                 event,
#                 min(100, score),
#                 "advanced kinematic impact verified"
#             )

#         return self.reject(
#             event,
#             "candidate rejected",
#             score=min(100, score)
#         )

#     def accept(
#         self,
#         event,
#         score,
#         reason
#     ):

#         event = dict(event)

#         event["verified"] = True

#         event[
#             "verification_source"
#         ] = "advanced_kinematic"

#         event[
#             "verification_score"
#         ] = score

#         event[
#             "verification_reason"
#         ] = reason

#         event["collision_score"] = max(
#             event.get(
#                 "collision_score",
#                 0
#             ),
#             score
#         )

#         return event

#     def reject(
#         self,
#         event,
#         reason,
#         score=0
#     ):

#         event = dict(event)

#         event["verified"] = False

#         event[
#             "verification_source"
#         ] = "advanced_kinematic"

#         event[
#             "verification_score"
#         ] = score

#         event[
#             "verification_reason"
#         ] = reason

#         return event


# class SceneUnderstandingVerifier:

#     def __init__(self):

#         self.reasoner = (
#             CosmosReasoner()
#         )

#         self.fallback = (
#             LocalKinematicVerifier()
#         )

#     def verify(
#         self,
#         event,
#         frame=None,
#         clip_path=None
#     ):

#         if clip_path is None:

#             return self.fallback.verify(
#                 event,
#                 frame
#             )

#         cosmos_result = (
#             self.reasoner.verify(
#                 clip_path,
#                 event
#             )
#         )

#         collision = cosmos_result.get(
#             "collision",
#             False
#         )

#         cosmos_confidence = float(
#             cosmos_result.get(
#                 "confidence",
#                 0
#             )
#         )

#         verified_event = dict(event)

#         verified_event[
#             "verification_source"
#         ] = "cosmos_reason2_2b"

#         verified_event[
#             "verification_reason"
#         ] = cosmos_result.get(
#             "reason",
#             ""
#         )

#         verified_event[
#             "scene_summary"
#         ] = cosmos_result.get(
#             "scene_summary",
#             ""
#         )

#         verified_event[
#             "collision_type"
#         ] = cosmos_result.get(
#             "collision_type",
#             ""
#         )

#         verified_event[
#             "fault_estimation"
#         ] = cosmos_result.get(
#             "fault_estimation",
#             ""
#         )

#         verified_event[
#             "evidence"
#         ] = cosmos_result.get(
#             "evidence",
#             []
#         )

#         verified_event[
#             "verification_score"
#         ] = int(
#             cosmos_confidence * 100
#         )

#         # Hybrid fusion
#         kinematic_score = (
#             verified_event.get(
#                 "collision_score",
#                 0
#             )
#         )

#         hybrid_score = int(
#             (
#                 0.45 * kinematic_score
#                 +
#                 0.55 * (
#                     cosmos_confidence * 100
#                 )
#             )
#         )

#         verified_event[
#             "hybrid_score"
#         ] = hybrid_score

#         verified_event["verified"] = (
#             collision and
#             hybrid_score >= 75
#         )

#         return verified_event


# class CollisionVerificationPipeline:

#     def __init__(
#         self,
#         verifier=None,
#         keep_rejected=False
#     ):

#         self.verifier = (
#             verifier or
#             LocalKinematicVerifier()
#         )

#         self.keep_rejected = (
#             keep_rejected
#         )

#     def verify_events(
#         self,
#         events,
#         frame=None,
#         clip_path=None
#     ):

#         verified_events = []

#         for event in events:

#             verified = (
#                 self.verifier.verify(
#                     event,
#                     frame=frame,
#                     clip_path=clip_path
#                 )
#             )

#             if (
#                 verified.get("verified")
#                 or
#                 self.keep_rejected
#             ):

#                 verified_events.append(
#                     verified
#                 )

#         return verified_events



class LocalKinematicVerifier:

    """
    Advanced second-stage kinematic verifier.
    """

    def __init__(
        self,
        confirmation_threshold=84
    ):

        self.confirmation_threshold = (
            confirmation_threshold
        )

    def verify(
        self,
        event,
        frame=None
    ):

        features = event.get(
            "candidate_features",
            {}
        )

        # Immediate rejection
        if features.get(
            "parallel_side_by_side"
        ):

            return self.reject(
                event,
                "parallel traffic flow"
            )

        score = event.get(
            "collision_score",
            0
        )

        # Spatial evidence
        if features.get("near_enough"):
            score += 6

        if features.get("approaching"):
            score += 10

        if features.get("closing_now"):
            score += 6

        # Strong impact evidence
        if features.get(
            "hard_deceleration"
        ):
            score += 16

        if features.get(
            "speed_collapse"
        ):
            score += 18

        if features.get(
            "direction_change"
        ):
            score += 14

        if features.get(
            "sudden_stop"
        ):
            score += 14

        # Low-speed impact evidence
        if features.get(
            "micro_impact"
        ):
            score += 16

        if features.get(
            "post_impact_pause"
        ):
            score += 12

        if features.get(
            "rebound_separation"
        ):
            score += 14

        # Strong suppression
        if features.get(
            "parallel_side_by_side"
        ):
            score -= 70

        impact_evidence = any([

            features.get(
                "hard_deceleration"
            ),

            features.get(
                "speed_collapse"
            ),

            features.get(
                "direction_change"
            ),

            features.get(
                "micro_impact"
            ),

            features.get(
                "post_impact_pause"
            ),

            features.get(
                "rebound_separation"
            )
        ])

        spatial_evidence = (
            features.get("near_enough")
            and
            (
                features.get("approaching")
                or
                features.get("closing_now")
            )
        )

        verified = (
            score >= self.confirmation_threshold
            and
            impact_evidence
            and
            spatial_evidence
        )

        if verified:

            return self.accept(
                event,
                min(100, score),
                "advanced kinematic impact verified"
            )

        return self.reject(
            event,
            "candidate rejected",
            score=min(100, score)
        )

    def accept(
        self,
        event,
        score,
        reason
    ):

        event = dict(event)

        event["verified"] = True

        event[
            "verification_source"
        ] = "advanced_kinematic"

        event[
            "verification_score"
        ] = score

        event[
            "verification_reason"
        ] = reason

        event["collision_score"] = max(
            event.get(
                "collision_score",
                0
            ),
            score
        )

        return event

    def reject(
        self,
        event,
        reason,
        score=0
    ):

        event = dict(event)

        event["verified"] = False

        event[
            "verification_source"
        ] = "advanced_kinematic"

        event[
            "verification_score"
        ] = score

        event[
            "verification_reason"
        ] = reason

        return event


class CollisionVerificationPipeline:

    def __init__(
        self,
        verifier=None,
        keep_rejected=False
    ):

        self.verifier = (
            verifier or
            LocalKinematicVerifier()
        )

        self.keep_rejected = (
            keep_rejected
        )

    def verify_events(
        self,
        events,
        frame=None
    ):

        verified_events = []

        for event in events:

            verified = (
                self.verifier.verify(
                    event,
                    frame=frame
                )
            )

            if (
                verified.get("verified")
                or
                self.keep_rejected
            ):

                verified_events.append(
                    verified
                )

        return verified_events