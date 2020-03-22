import React from "react";
import { connect } from 'react-redux'
import { withRouter } from "react-router";

import { ItemComp } from '../components'
import * as Actions from '../actions/Item'
import * as Constants from '../constants/Item'

export class Item extends React.Component {
  constructor(props) {
    super(props);

    //bind handler
    this.handleNew = this.handleNew.bind(this);
    this.handleEdit = this.handleEdit.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleReloadList = this.handleReloadList.bind(this);
    this.handleFormSave = this.handleFormSave.bind(this);
    this.handleRemoveItemImg = this.handleRemoveItemImg.bind(this);
  };

  componentDidMount() {
    this.getItemList()
  }

  getItemList() {
    this.props.sagaGetItemList(this.props.spaceId);
  }

  handleFormSave(values) {
    //add img into file list
    let fileMap = new Map();
    if(values.imgFile!=null && values.imgFile.size>0){
      fileMap.set('imgFile',values.imgFile);
    }

    //remove field from data 
    delete values.imgFile;

    //remove frontend use field
    delete values.formMode;

    //add current space id
    values.spaceId = this.props.spaceId;

    if (values.itemId != null) {
      //update
      this.props.sagaUpdateItem(values, fileMap);
    } else {
      //add new
      this.props.sagaAddItem(values, fileMap);
    }
  };

  handleDelete(itemId) {
    this.props.sagaDeleteItem(this.props.spaceId, itemId);
  }

  handleEdit(itemId) {
    this.props.sagaGetItem(itemId);
  }

  handleRemoveItemImg(itemId) {
    this.props.sagaRemoveItemImg(itemId);
  }

  handleReloadList(event){
    this.getItemList()
  }

  //UI only
  handleNew(event) {
    this.props.updateFormMode(Constants.FORM_EDIT_MODE);
  };
  handleCancel(event) {
    this.props.updateFormMode(Constants.FORM_READONLY_MODE);
  };


  render() {
    const itemList = this.props.itemList;
    const editStatus = this.props.editStatus;
    const formState = this.props.formState;
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
    )
  }
}

const mapStateToProps = (state) => {
  // //TODO: testing
  let spaceId = 1;

  let {itemList, editStatus} = state.Item;

  const inState = state.Item;
  let formState = {
    formMode: inState.formMode,
    itemId: inState.itemId,
    name: inState.name,
    colorCode: inState.colorCode,
    imageUrl: inState.imageUrl,
    imgFile: inState.imgFile,
    imgDisplayUrl: inState.imgDisplayUrl,
    tags: inState.tags,
    description: inState.description,
    category: inState.category,
    reminderDtm: inState.reminderDtm
  };

  //convert string into date object
  if(formState.reminderDtm!=null && formState.reminderDtm!==''){
    formState.reminderDtm = new Date(formState.reminderDtm);
  }

  return {
    spaceId: spaceId,
    itemList: itemList,
    editStatus: editStatus,
    formState: formState
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    sagaGetItemList: (spaceId) => {
      dispatch(Actions.sagaGetItemList(spaceId));
    },
    sagaUpdateItem: (item,fileMap) =>{
      dispatch(Actions.sagaUpdateItem(item, fileMap));
    },
    sagaAddItem: (item,fileMap) =>{
      dispatch(Actions.sagaAddItem(item, fileMap));
    },
    sagaDeleteItem: (spaceId, itemId) =>{
      dispatch(Actions.sagaDeleteItem(spaceId, itemId));
    },
    sagaGetItem: (itemId) =>{
      dispatch(Actions.sagaGetItem(itemId));
    },
    sagaRemoveItemImg:(itemId) =>{
      dispatch(Actions.sagaRemoveItemImg(itemId));
    },
    updateFormMode: (mode) => {
      dispatch(Actions.updateFormMode(mode));
    }
  }
}

export default withRouter(
  connect(
    mapStateToProps, mapDispatchToProps
  )(Item)
)