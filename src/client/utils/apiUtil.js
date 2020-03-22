import axios from 'axios';
import OperationResult from '../utils/operationResult';

export const API_HOST =  'http://localhost:8080';
export const API_INVOKE_TYPE_GET = 'GET';
export const API_INVOKE_TYPE_POST = 'POST';
export const API_INVOKE_TYPE_PUT = 'PUT';
export const API_INVOKE_TYPE_DELETE = 'DELETE';

//item related
export const API_ITEM_CONTEXT_PATH = '/item/';
export const API_ITEM_FULL_PATH = API_HOST + API_ITEM_CONTEXT_PATH;
export const API_ITEM = {
    GET_ITEM_LIST_BY_SPACE_ID: API_ITEM_FULL_PATH + 'spaces/',
    GET_ITEM: API_ITEM_FULL_PATH,
    ADD_ITEM: API_ITEM_FULL_PATH,
    UPDATE_ITEM: API_ITEM_FULL_PATH,
    DELETE_ITEM: API_ITEM_FULL_PATH,
    REMOVE_ITEM_IMG: API_ITEM_FULL_PATH + 'img/'
}

//space related
export const API_SPACE_CONTEXT_PATH = '/space/';
export const API_SPACE_FULL_PATH = API_HOST + API_SPACE_CONTEXT_PATH;
export const API_SPACE = {
    GET_SPACE_LIST_BY_USER_ID: API_SPACE_FULL_PATH + 'users/',
    GET_SPACE: API_SPACE_FULL_PATH,
    ADD_SPACE: API_SPACE_FULL_PATH,
    UPDATE_SPACE: API_SPACE_FULL_PATH,
    DELETE_SPACE: API_SPACE_FULL_PATH
}


//reminder related
export const API_REMINDER_CONTEXT_PATH = '/reminder/';
export const API_REMINDER_FULL_PATH = API_HOST + API_REMINDER_CONTEXT_PATH;
export const API_REMINDER = {
    GET_REMINDER_LIST_BY_USER_ID: API_REMINDER_FULL_PATH + 'users/',
    UPDATE_REMINDER: API_REMINDER_FULL_PATH,
}


export const invokeApi = async (invokeMethod, url, data, fileMap = null) => {
    const operResult = new OperationResult();

    try {
        let response = null;
        let formData = null;
        let headerConfig = null; 

        //prepare axios data and header config
        if(fileMap == null){
            formData = {data};
        }else{
            formData = new FormData();
            formData.append('data',JSON.stringify(data));

            //append file
            for (const [key, value] of fileMap.entries()) {
                formData.append(key,value);
            }

            headerConfig = {
                headers: {
                    'content-type': 'multipart/form-data'
                }
            }
        }
        
        switch (invokeMethod){
            case API_INVOKE_TYPE_GET:
                response = await axios.get(url);
                break;
            case API_INVOKE_TYPE_POST:
                response = await axios.post(url, formData, headerConfig);
                break;
            case API_INVOKE_TYPE_PUT:
                response = await axios.put(url, formData, headerConfig);
                break;
            case API_INVOKE_TYPE_DELETE:
                response = await axios.delete(url);
                break;
        }
        
        if (response.status >= 400 || !response.data.isSuccess) {
            operResult.setFail(response.message);
        }else{
            if(response.data.isSuccess){
                operResult.setSuccess(response.data.payload);
            }else{
                operResult.setFail(response.message);
            }
        }
    }catch (e) {
        if (e.response==null){
            operResult.setFail(e.message);
        }else if (e.response.status >= 400) {
            const {data = {}} = e.response
            operResult.setFail(data.error);
        }
    }finally{
        return operResult;
    }
};
