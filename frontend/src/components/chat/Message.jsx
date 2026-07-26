import MessageBubble from "./MessageBubble";

export default function Message({ message, onContactSubmit }) {
  return (
    <MessageBubble
      messageId={message.id}
      role={message.role}
      content={message.content}
      sources={message.sources}
      escalated={message.escalated}
      queryId={message.queryId}
      contactRequired={message.contactRequired}
      contactCollected={message.contactCollected}
      contactError={message.contactError}
      awaitingOfficer={message.awaitingOfficer}
      officerReply={message.officerReply}
      onContactSubmit={onContactSubmit}
    />
  );
}
