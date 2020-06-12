import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';
import { toast } from 'react-toastify';
import { GridComp } from '../components';
import * as Actions from '../actions/Grid';
import * as Constants from '../constants/Grid';
import * as UIConstants from '../constants/Global';
import * as AuthHelper from '../utils/AuthHelper';


export class Grid extends React.Component {
  constructor(props) {
    super(props);

    // space grid
    this.state = {
      itemCount: 0,
      tempLayouts: [],
      dataMap: new Map(),
      gridImgPath: null,
      isResetLayout: false,
      isDirtyWrite: false,
      currMode: Constants.FORM_READONLY_MODE,
      displayMsg: { isSuccess: null, msg: null }
    };

    this.handleNew = this.handleNew.bind(this);
    this.handleSave = this.handleSave.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleUpdateLayout = this.handleUpdateLayout.bind(this);
    this.handleSelect = this.handleSelect.bind(this);
    this.handleToggleMode = this.handleToggleMode.bind(this);
    this.handleRemove = this.handleRemove.bind(this);
    this.handleGoBack = this.handleGoBack.bind(this);
  }

  componentDidMount() {
    if (AuthHelper.validateUser(this.props.currentJwt, this.props.history)) {
      this.props.sagaGetGridList(this.props.spaceId);
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

      // clear header first
      this.updateHeaderMsgInUI(null, null);

      // delete case
      if (currStatus.operation === Constants.OPERATION_DELETE) {
        // delete success - remove in UI
        this.cbDeleteGridInUI(currStatus.isSuccess, `${currStatus.isSuccess ? currStatus.data.gridId : null}`);
      } else if (currStatus.operation === Constants.OPERATION_GET) {
        // get case
        this.cbLoadGridLayoutInUI(currStatus.isSuccess, currStatus.data);
      } else if (currStatus.operation === Constants.OPERATION_SAVE) {
        // save case
        this.cbSaveGridInUI(currStatus.isSuccess, currStatus.data);
      }
    }
  }

  handleCancel() {
    this.props.sagaGetGridList(this.props.spaceId);
  }

  handleGoBack() {
    this.props.history.push('/space');
  }

  handleUpdateLayout(layout) {
    this.setState({ tempLayouts: layout });
    if (this.state.isResetLayout) {
      // update layout by reset data from backend
      this.setState({ isResetLayout: false });
    } else {
      // this update layout not triggered by reset data
      this.setState({ isDirtyWrite: true });
    }
  }

  handleSelect(gridId) {
    this.props.setCurrentGridId(gridId);
    this.props.history.push('/item');
  }

  handleSave() {
    const allowAttr = ['x', 'y', 'w', 'h', 'i'];
    const data = {};
    const gridsArr = [];
    for (const el of this.state.tempLayouts) {
      for (const [key, value] of Object.entries(el)) {
        if (!allowAttr.includes(key)) {
          delete el[key];
        }
      }
      // generate each grid
      const grid = {
        layout: el,
        gridId: (parseInt(el.i, 10) < 0 ? null : parseInt(el.i, 10)),
        spaceId: this.props.spaceId
      };

      // push as list
      gridsArr.push(grid);
    }

    data.grids = gridsArr;
    this.props.sagaSaveGrids(data);
  }

  handleNew() {
    let nextId = this.state.itemCount;
    nextId -= 1;

    const newGrid = {
      w: 1, h: 1, x: 0, y: Infinity, i: `${nextId}`
    };// puts it at the bottom


    const tempList = [...this.state.tempLayouts].map(l => ({ ...l, static: false }));
    tempList.push(newGrid);

    this.setState({
      itemCount: nextId,
      tempLayouts: tempList,
      currMode: Constants.FORM_EDIT_MODE
    });
  }

  handleRemove(itemKey) {
    // keep at least 1 element
    if (this.state.tempLayouts.length === 1) {
      alert('Fail to delete, at least one grid in your space!');
      return;
    }

    // convert new grid id (<0) to positive with 'New'
    let displayId = itemKey;
    if (itemKey < 0) {
      displayId = `New ${(Math.abs(itemKey) - 1).toString().padStart(2, '0')}`;
    }

    const result = confirm(`Confirm to delete (Grid Id: ${displayId})?`);
    if (result === true) {
      // confirm
      if (itemKey > 0) {
        // delete from db first
        this.props.sagaDeleteGrid(itemKey);
      } else {
        // delete directly (new grid)
        this.cbDeleteGridInUI(true, itemKey);
      }
    }
  }

  handleToggleMode(currMode) {
    // change from edit to read
    if (currMode === Constants.FORM_READONLY_MODE && this.state.isDirtyWrite) {
      const result = confirm('Changes you made may not be saved. Are you sure you want to restore to original layout?');
      if (result === true) {
        // confirm to reset
        this.props.sagaGetGridList(this.props.spaceId);
      }
      return;
    }

    const list = this.state.tempLayouts.map(l => ({ ...l, static: (currMode === Constants.FORM_READONLY_MODE) }));

    this.setState({
      tempLayouts: list,
      currMode,
      isResetLayout: true
    });
  }

  // ------------------------------------------
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

  // triggered by did update after saga ajax call
  cbLoadGridLayoutInUI(isSuccess, grids) {
    if (!isSuccess) {
      this.updateHeaderMsgInUI(false, 'Failed to load grid. Please try again.');
      return;
    }

    let tempLayouts = null;
    let gridImgPath = null;
    let currMode = null;
    const dataMap = new Map();
    const counter = -2;

    // no record from db, prepare default new grid
    if (grids === null || grids.length === 0) {
      tempLayouts = [{
        w: 1, h: 1, x: 0, y: 0, i: `${counter}`
      }]; // puts it at the bottom

      // set as edit mode
      currMode = Constants.FORM_EDIT_MODE;
    } else {
      // load record from db

      // extract image path for display
      gridImgPath = grids[0].imgPath;

      const layouts = [];
      for (const grid of grids) {
        // prepare grid layouts
        layouts.push(grid.layout);

        // push in map for component to form UI
        dataMap.set(`${grid.gridId}`, grid);
      }

      // load data and set as view mode
      currMode = Constants.FORM_READONLY_MODE;
      tempLayouts = layouts.map(el => ({ ...el, static: true }));
    }

    this.setState({
      itemCount: counter,
      tempLayouts,
      dataMap,
      gridImgPath,
      currMode,
      isDirtyWrite: false,
      isResetLayout: true // prevent cause dirty write by layout reload
    });
  }

  cbSaveGridInUI(isSuccess, grids) {
    if (isSuccess) {
      // success, load new gridlayout with data
      this.cbLoadGridLayoutInUI(true, grids);
      this.updateHeaderMsgInUI(true, 'Save successfully.');
      this.setState({ isDirtyWrite: false });
    } else {
      this.updateHeaderMsgInUI(false, 'Failed to save grid. Please try again.');
    }
  }

  cbDeleteGridInUI(isSuccess, itemKey) {
    if (isSuccess) {
      // filter item by i(grid id in String)
      const orignList = [...this.state.tempLayouts];
      const tempList = orignList.filter(el => el.i !== itemKey);

      this.setState({
        tempLayouts: tempList,
        isResetLayout: true // prevent cause dirty write by layout reload
      });
      this.updateHeaderMsgInUI(true, `Grid ${itemKey < 0 ? '' : `(ID: ${itemKey})`} delete successfully`);
    } else {
      // fail to delete
      this.updateHeaderMsgInUI(false, 'Failed to delete grid. Please try again.');
    }
  }

  // space grid end
  render() {
    const {
      tempLayouts, dataMap, gridImgPath, isDirtyWrite, currMode, displayMsg
    } = this.state;
    const { pageLoading } = this.props;
    return (
      <div>
        <GridComp
          handleNew={this.handleNew}
          handleToggleMode={this.handleToggleMode}
          handleSave={this.handleSave}
          handleCancel={this.handleCancel}
          handleUpdateLayout={this.handleUpdateLayout}
          handleRemove={this.handleRemove}
          handleSelect={this.handleSelect}
          handleGoBack={this.handleGoBack}
          displayMsg={displayMsg}
          pageLoading={pageLoading}
          tempLayouts={tempLayouts}
          dataMap={dataMap}
          gridImgPath={gridImgPath}
          isDirtyWrite={isDirtyWrite}
          currMode={currMode}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  const { editStatus, pageLoading } = state.Grid;
  let { currentSpaceId } = state.Space;

  // TODO: testing only
  if (currentSpaceId == null) currentSpaceId = 1;

  const { currentJwt } = state.Auth;

  return {
    spaceId: currentSpaceId,
    editStatus,
    pageLoading,
    currentJwt
  };
};

const mapDispatchToProps = dispatch => ({
  sagaGetGridList: (spaceId) => {
    dispatch(Actions.sagaGetGridList(spaceId));
  },
  sagaSaveGrids: (grids) => {
    dispatch(Actions.sagaSaveGrids(grids));
  },
  sagaDeleteGrid: (gridId) => {
    dispatch(Actions.sagaDeleteGrid(gridId));
  },
  setCurrentGridId: (gridId) => {
    dispatch(Actions.setCurrentGridId(gridId));
  }
});


Grid.defaultProps = {
  currentJwt: null
};

Grid.propTypes = {
  currentJwt: PropTypes.oneOfType([PropTypes.object]),
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  history: PropTypes.oneOfType([PropTypes.object]).isRequired,
  spaceId: PropTypes.number.isRequired,
  pageLoading: PropTypes.bool.isRequired,
  sagaSaveGrids: PropTypes.func.isRequired,
  sagaGetGridList: PropTypes.func.isRequired,
  sagaDeleteGrid: PropTypes.func.isRequired,
  setCurrentGridId: PropTypes.func.isRequired
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Grid));
