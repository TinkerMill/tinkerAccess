use crate::messages::events::TAEvent;
#[cfg(feature = "ssr")]
use axum::extract::ws::CloseFrame;
#[cfg(feature = "ssr")]
use axum::Router;
#[cfg(feature = "ssr")]
use axum::{
    extract::ws::{Message, WebSocket, WebSocketUpgrade},
    response::IntoResponse,
    routing::get,
};

// WebSocketUpgrade: Extractor for establishing WebSocket connections.
#[cfg(feature = "ssr")]
pub async fn websocket_handler(ws: WebSocketUpgrade) -> impl IntoResponse {
    // Finalize upgrading the connection and call the provided callback with the stream.
    ws.on_failed_upgrade(|error| println!("Error upgrading websocket: {}", error))
        .on_upgrade(handle_socket)
}

// WebSocket: A stream of WebSocket messages.
#[cfg(feature = "ssr")]
async fn handle_socket(mut socket: WebSocket) {
    // Returns `None` if the stream has closed.
    while let Some(msg) = socket.recv().await {
        if let Ok(msg) = msg {
            match msg {
                Message::Text(utf8_bytes) => {
                    // let event: TAEvent = serde_json::from_str(utf8_bytes.as_str());
                    // match event {
                    match serde_json::from_str(utf8_bytes.as_str()) {
                        Ok(TAEvent::EventReportBinary {
                            header,
                            event_trigger,
                        }) => todo!(),
                        Ok(TAEvent::EventReportDisp {
                            header,
                            event_trigger,
                        }) => todo!(),
                        Ok(TAEvent::EventReportLed {
                            header,
                            event_trigger,
                        }) => todo!(),
                        Ok(TAEvent::EventReportCard {
                            header,
                            event_trigger,
                        }) => todo!(),
                        Ok(TAEvent::EventReportPostBoot {
                            header,
                            event_trigger,
                        }) => todo!(),
                        Ok(TAEvent::SetStateCmd { header, settings }) => todo!(),
                        Ok(TAEvent::BadCmd {
                            header,
                            cmd_msg_type,
                            cmd_ulid,
                            succeeded,
                            error_message,
                        }) => todo!(),
                        Ok(TAEvent::GetStateCmd { header }) => todo!(),
                        Ok(TAEvent::StateReport {
                            header,
                            boot_state,
                            current_io_state,
                        }) => todo!(),
                        Ok(TAEvent::SetConfigCmd { header, config }) => todo!(),
                        Ok(TAEvent::SetDefaultConfigCmd { header, config }) => todo!(),
                        Ok(TAEvent::GetConfigCmd { header }) => todo!(),
                        Ok(TAEvent::ConfigReport {
                            header,
                            config,
                            device_info,
                        }) => todo!(),
                        Err(err) => todo!(),
                    }
                }
                Message::Binary(bytes) => {
                    println!("Received bytes of length: {}", bytes.len());
                    let result = socket
                        .send(Message::Text(
                            format!("Received bytes of length: {}", bytes.len()).into(),
                        ))
                        .await;
                    if let Err(error) = result {
                        println!("Error sending: {}", error);
                        send_close_message(socket, 1011, &format!("Error occured: {}", error))
                            .await;
                        break;
                    }
                }
                // Close, Ping, Pong will be handled automatically
                // Message::Close
                // After receiving a close frame, axum will automatically respond with a close frame if necessary (you do not have to deal with this yourself).
                // After sending a close frame, you may still read messages, but attempts to send another message will error.
                // Since no further messages will be received, you may either do nothing or explicitly drop the connection.
                _ => {}
            }
        } else {
            let error = msg.err().unwrap();
            println!("Error receiving message: {:?}", error);
            send_close_message(socket, 1011, &format!("Error occured: {}", error)).await;
            break;
        }
    }
}

// We MAY “uncleanly” close a WebSocket connection at any time by simply dropping the WebSocket, ie: Break out of the recv loop.
// However, you may also use the graceful closing protocol, in which
// peer A sends a close frame, and does not send any further messages;
// peer B responds with a close frame, and does not send any further messages;
// peer A processes the remaining messages sent by peer B, before finally
// both peers close the connection.
//
// Close Code: https://kapeli.com/cheat_sheets/WebSocket_Status_Codes.docset/Contents/Resources/Documents/index
#[cfg(feature = "ssr")]
async fn send_close_message(mut socket: WebSocket, code: u16, reason: &str) {
    _ = socket
        .send(Message::Close(Some(CloseFrame {
            code: code,
            reason: reason.into(),
        })))
        .await;
}
