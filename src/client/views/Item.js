import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import { toast } from 'react-toastify';
import { ItemComp } from '../components';
import * as Actions from '../actions/Item';
import * as Constants from '../constants/Item';
import * as UIConstants from '../constants/Global';
import * as AuthHelper from '../utils/AuthHelper';

export class Item extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      displayMsg: { isSuccess: null, msg: null }
    };

    // bind handler
    this.handleNew = this.handleNew.bind(this);
    this.handleEdit = this.handleEdit.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleReloadList = this.handleReloadList.bind(this);
    this.handleFormSave = this.handleFormSave.bind(this);
    this.handleRemoveItemImg = this.handleRemoveItemImg.bind(this);
    this.handleGoBack = this.handleGoBack.bind(this);
  }

  componentDidMount() {
    if (AuthHelper.validateUser(this.props.currentJwt, this.props.history)) {
      this.getItemList();
    }
  }

  componentDidUpdate(prevProps, prevState) {
    // handle side effect
    const currStatus = this.props.editStatus;

    // capture 1st side effect
    if (prevProps.editStatus.isSuccess !== currStatus.isSuccess
      && prevProps.editStatus.isSuccess == null) {
      // console.log(`prevProps ${JSON.stringify(prevProps.editStatus)}`);
      // console.log(`currStatus ${JSON.stringify(currStatus)}`);

      // delete case
      if (currStatus.operation === Constants.OPERATION_DELETE) {
        this.updateHeaderMsgInUI(currStatus.isSuccess,
          currStatus.isSuccess
            ? 'Delete successfully.'
            : 'Failed to delete. Please try again.');
      } else if (currStatus.operation === Constants.OPERATION_REMOVE_IMG) {
        // remove img

      } else if (currStatus.operation === Constants.OPERATION_GET) {
        // get case, show error if failed
        if (!currStatus.isSuccess) {
          this.updateHeaderMsgInUI(false, 'Failed to load item. Please try again.');
        }
      } else if (currStatus.operation === Constants.OPERATION_SAVE
        || currStatus.operation === Constants.OPERATION_UPDATE) {
        // save case
        this.updateHeaderMsgInUI(currStatus.isSuccess,
          currStatus.isSuccess
            ? 'Save successfully.'
            : 'Failed to save. Please try again.');
      }
    }
  }

  getItemList() {
    this.props.sagaGetItemList(this.props.gridId);
  }

  handleFormSave(values) {
    let fileMap = null;

    if (values.imgFile != null && values.imgFile.size > 0) {
      // add img into file map
      fileMap = new Map();
      fileMap.set('imgFile', values.imgFile);
    }

    // add current space id
    values.gridId = this.props.gridId;

    // clean up unecessary data fields
    delete values.imgFile; // to be passed by fileMap
    delete values.formMode;

    if (values.itemId != null) {
      // update
      this.props.sagaUpdateItem(values, fileMap);
    } else {
      // add new
      this.props.sagaAddItem(values, fileMap);
    }
  }

  handleDelete(itemId, itemName, itemDesc) {
    let msg = `Confirm to delete (${itemName})?`;
    if (itemDesc != null && itemDesc.length > 0) {
      msg += `\n ${itemDesc}`;
    }
    const result = confirm(msg);
    if (result === true) {
      // confirm
      this.props.sagaDeleteItem(this.props.gridId, itemId);
    }
  }

  handleEdit(itemId) {
    this.props.sagaGetItem(itemId);
  }

  handleRemoveItemImg(itemId) {
    const result = confirm('Confirm to delete image?');
    if (result === true) {
      // confirm
      this.props.sagaRemoveItemImg(itemId);
    }
  }

  handleReloadList() {
    this.updateHeaderMsgInUI(null, null);
    this.getItemList();
  }

  // UI only
  handleNew() {
    this.props.updateFormMode(Constants.FORM_EDIT_MODE);
  }

  handleCancel() {
    this.props.updateFormMode(Constants.FORM_READONLY_MODE);
    this.handleReloadList();
  }

  handleGoBack() {
    this.props.history.push('/grid');
  }

  // update UI
  updateHeaderMsgInUI(isSuccess, msg) {
    this.setState({
      displayMsg: { isSuccess, msg }
    });

    // for toastify
    if (isSuccess != null && msg != null) {
      if (isSuccess) {
        toast(`${msg}`, { autoClose: UIConstants.UI_NOTIFY_DIALOG_SHOW_DURATION });
      } else {
        toast.error(`${msg}`);
      }
    }
  }

  render() {
    const { displayMsg } = this.state;
    const {
      itemList, editStatus, formState, pageLoading
    } = this.props;
    return (
      <div>
        <ItemComp
          handleFormSave={this.handleFormSave}
          handleCancel={this.handleCancel}
          handleNew={this.handleNew}
          handleEdit={this.handleEdit}
          handleDelete={this.handleDelete}
          handleReloadList={this.handleReloadList}
          handleRemoveItemImg={this.handleRemoveItemImg}
          handleGoBack={this.handleGoBack}

          pageLoading={pageLoading}
          displayMsg={displayMsg}
          itemList={itemList}
          editStatus={editStatus}
          formState={formState}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  let { currentGridId } = state.Grid;

  // TODO: testing only
  if (currentGridId == null) currentGridId = 37;

  const { itemList, editStatus, pageLoading } = state.Item;

  const inState = state.Item;
  const formState = {
    formMode: inState.formMode,
    itemId: inState.itemId,
    name: inState.name,
    colorCode: inState.colorCode,
    imgFile: inState.imgFile,
    imgPath: inState.imgPath,
    tags: inState.tags,
    description: inState.description,
    category: inState.category,
    reminderDtm: inState.reminderDtm
  };

  // convert string into date object
  if (formState.reminderDtm != null && formState.reminderDtm !== '') {
    formState.reminderDtm = new Date(formState.reminderDtm);
  }

  const { currentJwt } = state.Auth;

  return {
    gridId: currentGridId,
    itemList,
    editStatus,
    formState,
    pageLoading,
    currentJwt
  };
};

const mapDispatchToProps = dispatch => ({
  sagaGetItemList: (gridId) => {
    dispatch(Actions.sagaGetItemList(gridId));
  },
  sagaUpdateItem: (item, fileMap) => {
    dispatch(Actions.sagaUpdateItem(item, fileMap));
  },
  sagaAddItem: (item, fileMap) => {
    dispatch(Actions.sagaAddItem(item, fileMap));
  },
  sagaDeleteItem: (gridId, itemId) => {
    dispatch(Actions.sagaDeleteItem(gridId, itemId));
  },
  sagaGetItem: (itemId) => {
    dispatch(Actions.sagaGetItem(itemId));
  },
  sagaRemoveItemImg: (itemId) => {
    dispatch(Actions.sagaRemoveItemImg(itemId));
  },
  updateFormMode: (mode) => {
    dispatch(Actions.updateFormMode(mode));
  }
});

Item.defaultProps = {
  itemList: [],
  currentJwt: null
};

Item.propTypes = {
  currentJwt: PropTypes.oneOfType([PropTypes.object]),
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  history: PropTypes.oneOfType([PropTypes.object]).isRequired,
  gridId: PropTypes.number.isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  itemList: PropTypes.arrayOf(PropTypes.object),
  updateFormMode: PropTypes.func.isRequired,
  sagaGetItemList: PropTypes.func.isRequired,
  sagaUpdateItem: PropTypes.func.isRequired,
  sagaAddItem: PropTypes.func.isRequired,
  sagaDeleteItem: PropTypes.func.isRequired,
  sagaGetItem: PropTypes.func.isRequired,
  sagaRemoveItemImg: PropTypes.func.isRequired
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Item));
