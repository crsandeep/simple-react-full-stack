export default class OperationResult {
  constructor() {
    this.setAttribute(false, null, null, null);
  }

  setSuccess(payload) {
    this.setAttribute(true, payload, null, null);
  }

  setFailWithPayload(payload, messageCd, message) {
    this.setAttribute(false, payload, messageCd, message);
  }

  setFail(messageCd, message) {
    this.setAttribute(false, null, messageCd, message);
  }

  setAttribute(isSuccess, payload, messageCd, message) {
    this.isSuccess = isSuccess;
    this.payload = payload;
    this.message = message;
    this.messageCd = messageCd;
  }

  getPayload() {
    return this.payload;
  }

  isSuccess() {
    return this.isSuccess;
  }

  getMessage() {
    return this.message;
  }


  getMessageCd() {
    return this.messageCd;
  }
}
