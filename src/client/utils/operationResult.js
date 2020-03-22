export default class OperationResult {

    constructor() {
        this.setAttribute(false, null, null);
    }

    setSuccess(data){
        this.setAttribute(true, data, null);
    }

    setFailWithData(data,message){
        this.setAttribute(false, data, message);
    }

    setFail(message){
        this.setAttribute(false, null, message);
    }

    setAttribute(isSuccess, data, message){
        this.isSuccess = isSuccess;
        this.data = data;
        this.message = message;
    }

  }