import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';
import { toast } from 'react-toastify';
import { SpaceComp } from '../components';
import * as Actions from '../actions/Space';
import * as Constants from '../constants/Space';
import * as UIConstants from '../constants/Global';
import * as AuthHelper from '../utils/AuthHelper';

export class Space extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      displayMsg: { isSuccess: null, msg: null }
    };

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
    if (AuthHelper.validateUser(this.props.currentJwt, this.props.history)) {
      this.getSpaceList();
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
          this.updateHeaderMsgInUI(false, 'Failed to load space. Please try again.');
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

  handleDelete(spaceId, spaceName) {
    const result = confirm(`Confirm to delete (Space: ${spaceName})?`);
    if (result === true) {
      // confirm
      this.props.sagaDeleteSpace(this.props.userId, spaceId);
    }
  }

  handleEdit(spaceId) {
    this.props.sagaGetSpace(spaceId);
  }

  handleSelect(spaceId) {
    this.props.setCurrentSpaceId(spaceId);
    this.props.history.push('/grid');
  }

  handleRemoveSpaceImg(spaceId) {
    const result = confirm('Confirm to delete image?');
    if (result === true) {
      // confirm
      this.props.sagaRemoveSpaceImg(spaceId);
    }
  }

  handleReloadList() {
    this.updateHeaderMsgInUI(null, null);
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

  // update UI
  updateHeaderMsgInUI(isSuccess, msg) {
    // for large display header msg
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
      spaceList, editStatus, formState, pageLoading
    } = this.props;
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
          displayMsg={displayMsg}
          spaceList={spaceList}
          editStatus={editStatus}
          formState={formState}
          pageLoading={pageLoading}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  // //TODO: testing
  const userId = 1;

  const { spaceList, editStatus, pageLoading } = state.Space;
  const { currentJwt } = state.Auth;

  const inState = state.Space;
  const formState = {
    formMode: inState.formMode,
    spaceId: inState.spaceId,
    name: inState.name,
    imgPath: inState.imgPath,
    location: inState.location
  };

  return {
    userId,
    spaceList,
    editStatus,
    formState,
    pageLoading,
    currentJwt
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
  spaceList: [],
  currentJwt: null
};

Space.propTypes = {
  currentJwt: PropTypes.oneOfType([PropTypes.object]),
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  spaceList: PropTypes.arrayOf(PropTypes.object),
  userId: PropTypes.number.isRequired,
  pageLoading: PropTypes.bool.isRequired,

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
