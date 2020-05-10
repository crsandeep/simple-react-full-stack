import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import SplitPane from 'react-split-pane';
import _ from 'lodash';
import axios from 'axios';
import { SpaceComp } from '../components';
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
    this.props.setCurrentSpaceId(spaceId);
    this.props.history.push('/grid');
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


  render() {
    const { spaceList, editStatus, formState } = this.props;
    return (
      <div>
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
  },
  setCurrentSpaceId: (spaceId) => {
    dispatch(Actions.setCurrentSpaceId(spaceId));
  }
});

Space.defaultProps = {
  spaceList: []
};

Space.propTypes = {
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  spaceList: PropTypes.arrayOf(PropTypes.object),
  userId: PropTypes.number.isRequired,

  sagaGetSpaceList: PropTypes.func.isRequired,
  sagaUpdateSpace: PropTypes.func.isRequired,
  sagaAddSpace: PropTypes.func.isRequired,
  sagaDeleteSpace: PropTypes.func.isRequired,
  sagaGetSpace: PropTypes.func.isRequired,
  sagaRemoveSpaceImg: PropTypes.func.isRequired,
  updateFormMode: PropTypes.func.isRequired,
  setCurrentSpaceId: PropTypes.func.isRequired
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Space));
