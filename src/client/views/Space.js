import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import SplitPane from 'react-split-pane';
import _ from 'lodash';
import { SpaceList, SpaceGrid } from '../components';
import * as Actions from '../actions/Space';
import * as Constants from '../constants/Space';

export class Space extends React.Component {
  constructor(props) {
    super(props);

    // space list
    this.handleNew = this.handleNew.bind(this);
    this.handleEdit = this.handleEdit.bind(this);
    this.handleDelete = this.handleDelete.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleReloadList = this.handleReloadList.bind(this);
    this.handleFormSave = this.handleFormSave.bind(this);
    this.handleRemoveSpaceImg = this.handleRemoveSpaceImg.bind(this);

    // space grid

    this.state = {
      gridLayout: {},
      gridList: [],
      itemCount: 0
    };
    this.handleGridNew = this.handleGridNew.bind(this);
    this.handleGridSave = this.handleGridSave.bind(this);
    this.handleGridCancel = this.handleGridCancel.bind(this);
    this.handleGridUpdateLayout = this.handleGridUpdateLayout.bind(this);
    this.handleGridSelect = this.handleGridSelect.bind(this);
    this.handleGridToggleMode = this.handleGridToggleMode.bind(this);
    this.handleGridRemove = this.handleGridRemove.bind(this);
  }

  componentDidMount() {
    this.getSpaceList();
  }

  // space list start
  getSpaceList() {
    this.props.sagaGetSpaceList(this.props.userId);
  }

  handleFormSave(values) {
    let fileMap = null;

    if (values.imgFile != null && values.imgFile.size > 0) {
      // add img into file map
      fileMap = new Map();
      fileMap.set('imgFile', values.imgFile);
    }

    // add current user id
    values.userId = this.props.userId;

    // clean up unecessary data fields
    delete values.imgFile; // to be passed by fileMap
    delete values.formMode;

    if (values.spaceId != null) {
      // update
      this.props.sagaUpdateSpace(values, fileMap);
    } else {
      // add new
      this.props.sagaAddSpace(values, fileMap);
    }
  }

  handleDelete(spaceId) {
    this.props.sagaDeleteSpace(this.props.userId, spaceId);
  }

  handleEdit(spaceId) {
    this.props.sagaGetSpace(spaceId);
  }

  handleSelect(spaceId) {
    console.log(`Select space ${spaceId}`);
    // this.props.history.push('/grid');
  }

  handleRemoveSpaceImg(spaceId) {
    this.props.sagaRemoveSpaceImg(spaceId);
  }

  handleReloadList() {
    this.getSpaceList();
  }

  // UI only
  handleNew() {
    this.props.updateFormMode(Constants.FORM_EDIT_MODE);
  }

  handleCancel() {
    this.props.updateFormMode(Constants.FORM_READONLY_MODE);
    this.handleReloadList();
  }
  // space list end

  // space grid start
  handleGridCancel() {
    // this.props.updateFormMode(Constants.FORM_READONLY_MODE);
    // this.handleReloadList();
    this.setState({
      gridLayout: {},
      gridList: []
    });
    console.log(`handleGridCancel: ${JSON.stringify(this.state.gridList.length)} ---- ${JSON.stringify(this.state.gridLayout)}`);
  }

  handleGridUpdateLayout(currLayout, allLayouts) {
    this.setState({ gridLayout: allLayouts });
    console.log(`handleGridUpdateLayout: ${JSON.stringify(allLayouts)}`);
  }

  handleGridNew() {
    const nextId = this.state.itemCount + 1;
    const newGrid = {
      w: 1,
      h: 1,
      x: 0,
      y: Infinity, // puts it at the bottom
      i: `${nextId}`,
      minW: 1,
      maxW: 6,
      minH: 1,
      maxH: 6,
      moved: false,
      static: false
    };


    this.setState(prevState => ({
      itemCount: nextId,
      gridList: prevState.gridList.concat(newGrid)
    }));
    console.log(`handleGridNew: ${JSON.stringify(this.state.gridList)}`);
  }

  handleGridSelect(gridId) {
    console.log(`handleGridSelect: ${JSON.stringify(gridId)}`);
  }

  handleGridRemove(itemKey) {
    // event.stopPropagation();
    this.setState({
      // eslint-disable-next-line react/no-access-state-in-setstate
      gridList: _.reject(this.state.gridList, { i: itemKey })
      // itemCount: this.state.itemCount - 1
    });
    console.log(`handleGridRemove, ${itemKey}`);
  }

  handleGridToggleMode(isReadMode) {
    // update each grid layout
    let list = [];
    const obj = {};
    for (const attr in this.state.gridLayout) {
      list = (this.state.gridLayout[attr].map((el) => {
        el.static = isReadMode;
        return el;
      }));
      obj[attr] = list;
    }


    // gridlist
    let list2 = [];
    list2 = this.state.gridList.map((grid) => {
      grid.static = isReadMode;
      return grid;
    });

    this.setState({
      gridLayout: obj,
      gridList: list2
    });
  }

  handleGridSave() {
    console.log(`handleGridSave: ${JSON.stringify(this.state.gridLayout)}`);
  }

  // space grid end

  render() {
    const splitType = 'vertical';
    const initSize = 400;
    const spaceId = 1;

    const { gridList } = this.state;
    const { spaceList, editStatus, formState } = this.props;
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

              gridList={gridList}
              // gridLayout={this.state.gridLayout}
              spaceId={spaceId}
              formState={formState}
            />
          </div>
        </SplitPane>
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  // //TODO: testing
  const userId = 1;

  const { spaceList, editStatus } = state.Space;

  const inState = state.Space;
  const formState = {
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
    sizeDepth: inState.sizeDepth
  };

  return {
    userId,
    spaceList,
    editStatus,
    formState
  };
};

const mapDispatchToProps = dispatch => ({
  sagaGetSpaceList: (userId) => {
    dispatch(Actions.sagaGetSpaceList(userId));
  },
  sagaUpdateSpace: (space, fileMap) => {
    dispatch(Actions.sagaUpdateSpace(space, fileMap));
  },
  sagaAddSpace: (space, fileMap) => {
    dispatch(Actions.sagaAddSpace(space, fileMap));
  },
  sagaDeleteSpace: (userId, spaceId) => {
    dispatch(Actions.sagaDeleteSpace(userId, spaceId));
  },
  sagaGetSpace: (spaceId) => {
    dispatch(Actions.sagaGetSpace(spaceId));
  },
  sagaRemoveSpaceImg: (spaceId) => {
    dispatch(Actions.sagaRemoveSpaceImg(spaceId));
  },
  updateFormMode: (mode) => {
    dispatch(Actions.updateFormMode(mode));
  }
});

Space.propTypes = {
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  spaceList: PropTypes.arrayOf(PropTypes.object).isRequired,
  userId: PropTypes.number.isRequired,

  sagaGetSpaceList: PropTypes.func.isRequired,
  sagaUpdateSpace: PropTypes.func.isRequired,
  sagaAddSpace: PropTypes.func.isRequired,
  sagaDeleteSpace: PropTypes.func.isRequired,
  sagaGetSpace: PropTypes.func.isRequired,
  sagaRemoveSpaceImg: PropTypes.func.isRequired,
  updateFormMode: PropTypes.func.isRequired
};

export default withRouter(
  connect(
    mapStateToProps, mapDispatchToProps
  )(Space)
);
