import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import _ from 'lodash';
import axios from 'axios';
import { GridComp } from '../components';
import * as Actions from '../actions/Space';
import * as Constants from '../constants/Space';


export class Grid extends React.Component {
  constructor(props) {
    super(props);

    // space grid
    this.state = {
      itemCount: 0,
      tempLayouts: [],
      cuurSpaceId: 2
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
    this.loadGridRecord(this.state.cuurSpaceId);
  }

  // space grid start
  async getFromLS(spaceId) {
    // TODO:  Testing
    let result = null;
    await axios.get(`http://localhost:8080/api/grid/space/${spaceId}`)
      .then((response) => {
        if (response.data.payload.layouts != null && response.data.payload.layouts.length > 0) {
          result = response.data.payload.layouts;
        }
      }).catch((error) => {
        console.log(`ERROR: ${error}`);
      });
    return result;
  }

  saveToLS(spaceId) {
    const allowAttr = ['x', 'y', 'w', 'h', 'i'];
    const layouts = [];
    for (const el of this.state.tempLayouts) {
      for (const [key, value] of Object.entries(el)) {
        if (!allowAttr.includes(key)) {
          delete el[key];
        }
      }
      layouts.push(el);
    }

    axios.post('http://localhost:8080/api/grid/', {
      spaceId,
      layouts
    }).then((response) => {
      console.log(`Save ${JSON.stringify(response.data)}`);
      this.loadGridRecord(spaceId);
    }).catch((error) => {
      console.log(`ERROR: ${error}`);
    });
  }

  deleteGrid(gridId) {
    axios.delete(`http://localhost:8080/api/grid/${gridId}`, {
      gridId
    }).then((response) => {
      console.log(`Delete ${JSON.stringify(response.data)}`);
    }).catch((error) => {
      console.log(`ERROR: ${error}`);
    });
  }

  handleGridCancel() {
    this.loadGridRecord(this.state.cuurSpaceId);
  }

  handleGridUpdateLayout(layout) {
    console.log(`currLayout: ${JSON.stringify(layout)}`);
    this.setState({ tempLayouts: layout });
  }

  handleGridSelect(gridId) {
    console.log(`handleGridSelect: ${JSON.stringify(gridId)}`);
    this.props.history.push('/item');
  }

  handleGridSave() {
    this.saveToLS(this.state.cuurSpaceId, this.state.tempLayouts);
    console.log(`Save: ${JSON.stringify(this.state.tempLayouts)}`);
  }
  // ------------------------------------------


  async loadGridRecord(spaceId) {
    let originalLayouts = await this.getFromLS(spaceId);
    const counter = -1;

    if (originalLayouts === null) {
      // add one as default

      originalLayouts = [{
        w: 2,
        h: 1,
        x: 0,
        y: 0, // puts it at the bottom
        i: '-1'
      }];
    }

    this.setState({
      itemCount: counter,
      tempLayouts: originalLayouts
    });
  }

  handleGridNew() {
    let nextId = this.state.itemCount;
    nextId -= 1;

    const newGrid = {
      w: 2,
      h: 1,
      x: 0,
      y: Infinity, // puts it at the bottom
      i: `${nextId}`
    };

    const tempList = [...this.state.tempLayouts];
    tempList.push(newGrid);

    this.setState({
      itemCount: nextId,
      tempLayouts: tempList
    });
  }

  handleGridRemove(itemKey) {
    // keep at least 1 element
    if (this.state.tempLayouts.length === 1) {
      alert('Fail to delete, at least one grid in your space!');
      return;
    }

    let tempList = [...this.state.tempLayouts];
    tempList = tempList.filter(el => el.i !== itemKey);

    this.setState({
      tempLayouts: tempList
    });

    console.log(`handleGridRemove, ${itemKey}`);
    if (itemKey > 0) {
      this.deleteGrid(itemKey);
    }
  }

  handleGridToggleMode(isReadMode) {
    const list = this.state.tempLayouts.map(l => ({ ...l, static: isReadMode }));

    this.setState({
      tempLayouts: list
    });

    console.log(
      `handleGridToggleMode: ${JSON.stringify(this.state.tempLayouts)}`
    );
  }

  // space grid end

  render() {
    const splitType = 'vertical';
    const initSize = 400;
    const spaceId = 1;

    const { tempLayouts } = this.state;
    const { spaceList, editStatus, formState } = this.props;
    return (
      <div>
        <GridComp
          handleNew={this.handleGridNew}
          handleToggleMode={this.handleGridToggleMode}
          handleSave={this.handleGridSave}
          handleCancel={this.handleGridCancel}
          handleUpdateLayout={this.handleGridUpdateLayout}
          handleRemove={this.handleGridRemove}
          handleSelect={this.handleGridSelect}
          spaceId={spaceId}
          formState={formState}
          tempLayouts={tempLayouts}
        />
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
  // sagaGetSpaceList: (userId) => {
  //   dispatch(Actions.sagaGetSpaceList(userId));
  // },
  // sagaUpdateSpace: (space, fileMap) => {
  //   dispatch(Actions.sagaUpdateSpace(space, fileMap));
  // },
  // sagaAddSpace: (space, fileMap) => {
  //   dispatch(Actions.sagaAddSpace(space, fileMap));
  // },
  // sagaDeleteSpace: (userId, spaceId) => {
  //   dispatch(Actions.sagaDeleteSpace(userId, spaceId));
  // },
  // sagaGetSpace: (spaceId) => {
  //   dispatch(Actions.sagaGetSpace(spaceId));
  // },
  // sagaRemoveSpaceImg: (spaceId) => {
  //   dispatch(Actions.sagaRemoveSpaceImg(spaceId));
  // },
  // updateFormMode: (mode) => {
  //   dispatch(Actions.updateFormMode(mode));
  // }
});

Grid.defaultProps = {
  spaceList: []
};

Grid.propTypes = {
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  spaceList: PropTypes.arrayOf(PropTypes.object),
  userId: PropTypes.number.isRequired

  // sagaGetSpaceList: PropTypes.func.isRequired,
  // sagaUpdateSpace: PropTypes.func.isRequired,
  // sagaAddSpace: PropTypes.func.isRequired,
  // sagaDeleteSpace: PropTypes.func.isRequired,
  // sagaGetSpace: PropTypes.func.isRequired,
  // sagaRemoveSpaceImg: PropTypes.func.isRequired,
  // updateFormMode: PropTypes.func.isRequired
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Grid));
