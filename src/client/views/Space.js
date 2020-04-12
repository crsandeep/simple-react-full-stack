import React from "react";
import { connect } from 'react-redux'
import { withRouter } from "react-router";

import { SpaceComp } from '../components'
import * as Actions from '../actions/Space'
import * as Constants from '../constants/Space'

import SplitPane from 'react-split-pane'

export class Space extends React.Component {
  constructor(props) {
    super(props);

    //bind handler
    this.handleNew = this.handleNew.bind(this);
    this.handleEdit = this.handleEdit.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleReloadList = this.handleReloadList.bind(this);
    this.handleFormSave = this.handleFormSave.bind(this);
    this.handleRemoveSpaceImg = this.handleRemoveSpaceImg.bind(this);
  };

  componentDidMount() {
    this.getSpaceList()
  }

  getSpaceList() {
    this.props.sagaGetSpaceList(this.props.userId);
  }

  handleFormSave(values) {
    let fileMap = null;

    if(values.imgFile!=null && values.imgFile.size>0){
      //add img into file map
      fileMap = new Map();
      fileMap.set('imgFile',values.imgFile);
    }

    //add current user id
    values.userId = this.props.userId;

    //clean up unecessary data fields
    delete values.imgFile;  //to be passed by fileMap
    delete values.formMode;

    if (values.spaceId != null) {
      //update
      this.props.sagaUpdateSpace(values, fileMap);
    } else {
      //add new
      this.props.sagaAddSpace(values, fileMap);
    }
  };

  handleDelete(spaceId) {
    this.props.sagaDeleteSpace(this.props.userId, spaceId);
  }

  handleEdit(spaceId) {
    this.props.sagaGetSpace(spaceId);
  }

  handleSelect(spaceId) {
    console.log('Select space '+ spaceId)
    // this.props.history.push('/grid');
  };

  handleRemoveSpaceImg(spaceId) {
    this.props.sagaRemoveSpaceImg(spaceId);
  }

  handleReloadList(event){
    this.getSpaceList()
  }

  //UI only
  handleNew(event) {
    this.props.updateFormMode(Constants.FORM_EDIT_MODE);
  };
  
  handleCancel(event) {
    this.props.updateFormMode(Constants.FORM_READONLY_MODE);
    this.handleReloadList();
  };


  render() {
    const spaceList = this.props.spaceList;
    const editStatus = this.props.editStatus;
    const formState = this.props.formState;
    return (
      <div>
        <SplitPane split="vertical" defaultSize={400}>
        <div>
          {/* Left side bar */}
          <SpaceComp
            handleFormSave={this.handleFormSave}
            handleCancel={this.handleCancel}
            handleNew={this.handleNew}
            handleEdit={this.handleEdit}
            handleSelect={this.handleSelect}
            handleDelete={this.handleDelete}
            handleReloadList={this.handleReloadList}
            handleRemoveSpaceImg={this.handleRemoveSpaceImg}

            spaceList={spaceList}
            editStatus={editStatus}
            formState={formState}
          />
        </div>
        <div>
                            Hi 2
        </div>
        </SplitPane>
      </div>
    )
  }
}

const mapStateToProps = (state) => {
  // //TODO: testing
  let userId = 1;

  let {spaceList, editStatus} = state.Space;

  const inState = state.Space;
  let formState = {
    formMode: inState.formMode,
    spaceId: inState.spaceId,
    name: inState.name,
    colorCode: inState.colorCode,
    imgPath: inState.imgPath,
    tags: inState.tags,
    location: inState.location,
    sizeUnit: inState.sizeUnit,
    sizeWidth: inState.sizeWidth,
    sizeHeight: inState.sizeHeight,
    sizeDepth: inState.sizeDepth,
  };

  return {
    userId: userId,
    spaceList: spaceList,
    editStatus: editStatus,
    formState: formState
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    sagaGetSpaceList: (userId) => {
      dispatch(Actions.sagaGetSpaceList(userId));
    },
    sagaUpdateSpace: (space,fileMap) =>{
      dispatch(Actions.sagaUpdateSpace(space, fileMap));
    },
    sagaAddSpace: (space,fileMap) =>{
      dispatch(Actions.sagaAddSpace(space, fileMap));
    },
    sagaDeleteSpace: (userId, spaceId) =>{
      dispatch(Actions.sagaDeleteSpace(userId, spaceId));
    },
    sagaGetSpace: (spaceId) =>{
      dispatch(Actions.sagaGetSpace(spaceId));
    },
    sagaRemoveSpaceImg:(spaceId) =>{
      dispatch(Actions.sagaRemoveSpaceImg(spaceId));
    },
    updateFormMode: (mode) => {
      dispatch(Actions.updateFormMode(mode));
    }
  }
}

export default withRouter(
  connect(
    mapStateToProps, mapDispatchToProps
  )(Space)
)