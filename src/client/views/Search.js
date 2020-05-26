import React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router';
import PropTypes from 'prop-types';

import { SearchComp } from '../components';
import * as Actions from '../actions/Search';
import * as Constants from '../constants/Search';

export class Search extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      displayMsg: { isSuccess: null, msg: null },
      formState: {
        keyword: '',
        colorCode: '',
        tags: '',
        category: '',
        location: ''
      }
    };

    // bind handler
    this.handleSearch = this.handleSearch.bind(this);
    this.handleGoBack = this.handleGoBack.bind(this);
    this.handleClear = this.handleClear.bind(this);
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

      // delete case
      if (currStatus.operation === Constants.OPERATION_SEARCH) {
        if (!currStatus.isSuccess) {
          this.updateHeaderMsgInUI(false, 'Failed to Search item. Please try again.');
        }
      }
    }
  }

  handleSearch(values) {
    // add current space id
    values.userId = this.props.userId;
    this.props.sagaSearchItem(values);
  }

  handleClear() {
    this.props.clearItemList();
  }

  handleGoBack() {
    this.props.history.push('/space');
  }

  // update UI
  updateHeaderMsgInUI(isSuccess, msg) {
    this.setState({
      displayMsg: { isSuccess, msg }
    });
  }

  render() {
    const { displayMsg, formState } = this.state;
    const { itemList, editStatus, pageLoading } = this.props;
    return (
      <div>
        <SearchComp
          handleSearch={this.handleSearch}
          handleClear={this.handleClear}
          handleGoBack={this.handleGoBack}

          displayMsg={displayMsg}
          itemList={itemList}
          editStatus={editStatus}
          formState={formState}
          pageLoading={pageLoading}
        />
      </div>
    );
  }
}

const mapStateToProps = (state) => {
  // const { userId } = state.User;
  // //TODO: testing
  const userId = 1;

  const { itemList, editStatus, pageLoading } = state.Search;

  return {
    userId,
    itemList,
    editStatus,
    pageLoading
  };
};

const mapDispatchToProps = dispatch => ({
  sagaSearchItem: (values) => {
    dispatch(Actions.sagaSearchItem(values));
  },
  clearItemList: () => {
    dispatch(Actions.clearItemList());
  }
});

Search.defaultProps = {
  itemList: []
};

Search.propTypes = {
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  history: PropTypes.oneOfType([PropTypes.object]).isRequired,
  userId: PropTypes.number.isRequired,
  pageLoading: PropTypes.bool.isRequired,
  itemList: PropTypes.arrayOf(PropTypes.object),
  sagaSearchItem: PropTypes.func.isRequired,
  clearItemList: PropTypes.func.isRequired
};

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(Search));
