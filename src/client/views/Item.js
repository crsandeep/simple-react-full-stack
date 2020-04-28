import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';

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

  handleReloadList(event) {
    this.getItemList();
  }

  // UI only
  handleNew(event) {
    this.props.updateFormMode(Constants.FORM_EDIT_MODE);
  }

  handleCancel(event) {
    this.props.updateFormMode(Constants.FORM_READONLY_MODE);
    this.handleReloadList();
  }


  render() {
    const { itemList } = this.props;
    const { editStatus } = this.props;
    const { formState } = this.props;
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

          itemList={itemList}
          editStatus={editStatus}
          formState={formState}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  // //TODO: testing
  const gridId = 37;

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
    gridId,
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

export default withRouter(
  connect(
    mapStateToProps, mapDispatchToProps
  )(Item)
);
