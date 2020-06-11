import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import { toast } from 'react-toastify';
import { AuthComp } from '../components';
import * as Actions from '../actions/Auth';
import * as Constants from '../constants/Auth';
import * as MessageCd from '../constants/MessageCd';
import * as UIConstants from '../constants/Global';

export class Auth extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      displayMsg: { isLoginMode: null, isSuccess: null, msg: null }
    };

    // bind handler
    this.handleLogin = this.handleLogin.bind(this);
    this.handleRegister = this.handleRegister.bind(this);
  }

  componentDidMount() {
  }

  componentDidUpdate(prevProps, prevState) {
    // handle side effect
    const currStatus = this.props.editStatus;

    // capture 1st side effect
    if (prevProps.editStatus.isSuccess !== currStatus.isSuccess
      && prevProps.editStatus.isSuccess == null) {
      // console.log(`prevProps ${JSON.stringify(prevProps.editStatus)}`);
      // console.log(`currStatus ${JSON.stringify(currStatus)}`);

      this.setDisplayError();
      if (currStatus.operation === Constants.OPERATION_REGISTER) {
        if (!currStatus.isSuccess) {
          if (MessageCd.USER_EMAIL_ALREADY_EXIST === currStatus.messageCd) {
            this.setDisplayError(false, 'This Email already register');
          } else {
            this.setDisplayError(false, 'Failed to register. Please try again.');
            toast.error('Failed to register. Please try again.');
          }
        } else {
          this.props.handleClose();

          this.notifyMsg(true, 'Welcome to Space Master!');
        }
      } else if (currStatus.operation === Constants.OPERATION_LOGIN) {
        if (!currStatus.isSuccess) {
          if (MessageCd.USER_LOGIN_INVALID_CREDENTIAL === currStatus.messageCd) {
            this.setDisplayError(true, 'Invalid username or password.');
          } else {
            this.setDisplayError(true, 'Failed to login. Please try again.');
            this.notifyMsg(false, 'Failed to login. Please try again.', false);
          }
        } else {
          localStorage.setItem('currentUser', JSON.stringify(currStatus.data));
          this.props.handleClose();
          this.notifyMsg(true, `Welcome back ${currStatus.data.name}!`);
        }
      }
    }
  }

  // update UI
  setDisplayError(isLoginMode = null, msg = null) {
    this.setState({
      displayMsg: { isLoginMode, msg }
    });
  }

  notifyMsg(isSuccess, message, isAutoClose = true) {
    let configAutoClose = {};
    if (isAutoClose) {
      configAutoClose = { autoClose: UIConstants.UI_NOTIFY_DIALOG_SHOW_DURATION };
    }

    if (isSuccess) {
      toast(message, configAutoClose);
    } else {
      toast.error(message, configAutoClose);
    }
  }

  handleLogin(values) {
    this.props.sagaLogin(values);
  }

  handleRegister(values) {
    const inputs = Object.assign({}, values);
    delete inputs.verifyPassword; // remove password

    this.props.sagaRegister(inputs);
  }

  render() {
    const { displayMsg } = this.state;
    const { pageLoading } = this.props;
    return (
      <AuthComp
        isShow={this.props.isShow}
        displayMsg={displayMsg}
        pageLoading={pageLoading}
        handleClose={this.props.handleClose}
        handleLogin={this.handleLogin}
        handleRegister={this.handleRegister}
      />
    );
  }
}

const mapStateToProps = (state) => {
  const { editStatus, pageLoading } = state.Auth;

  return {
    editStatus,
    pageLoading
  };
};

const mapDispatchToProps = dispatch => ({
  sagaLogin: (values) => {
    dispatch(Actions.sagaLogin(values));
  },
  sagaRegister: (values) => {
    dispatch(Actions.sagaRegister(values));
  }
});

Auth.propTypes = {
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  pageLoading: PropTypes.bool.isRequired,
  isShow: PropTypes.bool.isRequired,
  handleClose: PropTypes.func.isRequired,
  sagaLogin: PropTypes.func.isRequired,
  sagaRegister: PropTypes.func.isRequired
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Auth));
