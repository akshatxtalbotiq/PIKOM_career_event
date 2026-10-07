"use client";

import AttendeePageLayout from "../../components/AttendeePageLayout";
import AttendeeTrainingView from "../../components/AttendeeTrainingView";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function TrainingProviders() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Training & Promotions" attendee={attendee}>
      {attendee.data && <AttendeeTrainingView providers={attendee.data.training_providers} me={attendee.me} busy={attendee.busy} action={attendee.action} />}
    </AttendeePageLayout>
  );
}
