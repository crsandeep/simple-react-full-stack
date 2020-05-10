import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import { ItemComp } from '../components';
import * as Actions from '../actions/Item';
import * as Constants from '../constants/Item';

export class Item extends React.Component {
  constructor(props) {
    super(props);

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
    this.getItemList();
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

  handleDelete(itemId) {
    this.props.sagaDeleteItem(this.props.gridId, itemId);
  }

  handleEdit(itemId) {
    this.props.sagaGetItem(itemId);
  }

  handleRemoveItemImg(itemId) {
    this.props.sagaRemoveItemImg(itemId);
  }

  handleReloadList() {
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

  render() {
    const { itemList, editStatus, formState } = this.props;
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

          itemList={itemList}
          editStatus={editStatus}
          formState={formState}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  const { currentGridId } = state.Grid;

  const { itemList, editStatus } = state.Item;

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

  return {
    gridId: currentGridId,
    itemList,
    editStatus,
    formState
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
  itemList: []
};

Item.propTypes = {
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
