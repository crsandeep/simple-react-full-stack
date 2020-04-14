import React from "react";
import { connect } from 'react-redux';
import { withRouter } from "react-router";

import { SpaceList,SpaceGrid } from '../components';
import * as Actions from '../actions/Space';
import * as Constants from '../constants/Space';

import SplitPane from 'react-split-pane';
import _ from "lodash";

export class Space extends React.Component {
  constructor(props) {
    super(props);

    //space list 
    this.handleNew = this.handleNew.bind(this);
    this.handleEdit = this.handleEdit.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleReloadList = this.handleReloadList.bind(this);
    this.handleFormSave = this.handleFormSave.bind(this);
    this.handleRemoveSpaceImg = this.handleRemoveSpaceImg.bind(this);

    //space grid

    this.state = {
        gridLayout: {},
        gridList: [],
        itemCount: 0,
    }
    this.handleGridNew = this.handleGridNew.bind(this);
    this.handleGridSave = this.handleGridSave.bind(this);
    this.handleGridCancel = this.handleGridCancel.bind(this);
    this.handleGridUpdateLayout = this.handleGridUpdateLayout.bind(this);
    this.handleGridSelect = this.handleGridSelect.bind(this);
    this.handleGridToggleMode = this.handleGridToggleMode.bind(this);
    this.handleGridRemove = this.handleGridRemove.bind(this);
  };

  componentDidMount() {
    this.getSpaceList()
  }

  //space list start
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
  //space list end

  //space grid start
  handleGridCancel(event) {
    // this.props.updateFormMode(Constants.FORM_READONLY_MODE);
    // this.handleReloadList();
    this.setState({ 
      gridLayout: {},
      gridList: []
    });
    console.log("handleGridCancel: "+ JSON.stringify(this.state.gridList.length) + " ---- "+ JSON.stringify(this.state.gridLayout));
  };

  handleGridUpdateLayout(currLayout,allLayouts) {
    this.setState({ gridLayout: allLayouts});
    console.log("handleGridUpdateLayout: "+ JSON.stringify(allLayouts));
  }
  
  handleGridNew(event) {
    let nextId = this.state.itemCount + 1;
    const newGrid = {
      w: 1,
      h: 1,
      x: 0,
      y: Infinity, // puts it at the bottom
      i: '' + nextId,
      minW: 1, 
      maxW: 6,
      minH: 1, 
      maxH: 6,
      moved:false,
      static:false
    };


    this.setState({
        itemCount: nextId
        , gridList: this.state.gridList.concat(newGrid)
    })
    console.log("handleGridNew: " + JSON.stringify(this.state.gridList))
  }

  handleGridSelect(gridId){
    console.log("handleGridSelect: "+ JSON.stringify(gridId));
  }

  handleGridRemove(itemKey){
    event.stopPropagation();
    this.setState({
        gridList:  _.reject(this.state.gridList, { i: itemKey }),
        // itemCount: this.state.itemCount - 1
    });
    console.log('handleGridRemove, ' + itemKey )
  }

  handleGridToggleMode(isReadMode){
    //update each grid layout
    let list = []
    let obj = {};
    for (var attr in this.state.gridLayout) {
      this.state.gridLayout[attr].map(el => {
        el.static = isReadMode;
        list.push(el)
      })
      obj[attr] = list;
    }

    this.setState({
      gridLayout: obj
    })

    //gridlist
    list = []
    this.state.gridList.map(grid => {
      grid.static = isReadMode;
      list.push(grid)
    })
    this.setState({
      gridList: list
    })
  }

  handleGridSave(event) {
    const gridLayout = this.state.gridLayout;
    console.log("handleGridSave: "+ JSON.stringify(gridLayout));
  };

  //space grid end

  render() {
    let splitType = 'vertical';
    let initSize = 400;
    let spaceId = 1;

    const spaceList = this.props.spaceList;
    const editStatus = this.props.editStatus;
    const formState = this.props.formState;
    return (
      <div>
        <SplitPane split={splitType} defaultSize={initSize}>
        <div>
          {/* Left side bar */}
          <SpaceList
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
          {/* Right side content */}
          <SpaceGrid
            handleNew={this.handleGridNew}
            handleToggleMode={this.handleGridToggleMode}
            handleSave={this.handleGridSave}
            handleCancel={this.handleGridCancel}
            handleUpdateLayout={this.handleGridUpdateLayout}
            handleRemove={this.handleGridRemove}
            handleSelect={this.handleGridSelect}

            gridList={this.state.gridList}
            // gridLayout={this.state.gridLayout}
            spaceId={spaceId}
            formState={formState}
          />
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