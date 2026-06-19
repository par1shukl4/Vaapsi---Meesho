from backend.models.domain import CaseStatus, NDRCase, ResolutionAction, ResolutionEvent


class CaseStateMachine:
    def apply_resolution(self, case: NDRCase, event: ResolutionEvent) -> NDRCase:
        case.add_resolution(event)
        if event.action in {
            ResolutionAction.REDELIVERY,
            ResolutionAction.ADDRESS_CORRECTION,
            ResolutionAction.PARTIAL_REFUND,
        }:
            case.status = CaseStatus.RESOLVED
        elif event.action in {ResolutionAction.ESCALATION, ResolutionAction.FRAUD_INVESTIGATION}:
            case.status = CaseStatus.ESCALATED
        elif event.action == ResolutionAction.RTO_CLOSURE:
            case.status = CaseStatus.CLOSED_RTO
        else:
            case.status = CaseStatus.IN_PROGRESS
        return case
