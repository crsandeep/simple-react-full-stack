import React from 'react';
import PropTypes from 'prop-types';

// ui
import '../css/Form.css';
import 'react-datepicker/dist/react-datepicker.css';
import {
  Spinner, Alert
} from 'react-bootstrap';

import { makeStyles } from '@material-ui/core/styles';


const useStyles = makeStyles(theme => ({
  drawerHeader: {
    display: 'flex',
    alignItems: 'center',
    padding: theme.spacing(0, 1),
    // necessary for content to be below app bar
    ...theme.mixins.toolbar,
    justifyContent: 'flex-end'
  }
}));
function BaseUIComp(props) {
  const classes = useStyles();

  return (
    <div>
      {/* // add space for padding app bar */}
      <div className={classes.drawerHeader} />

      { // display message
        props.displayMsg.isSuccess !== null ? (
          props.displayMsg.isSuccess === true ? (
            <Alert variant="success">
              {props.displayMsg.msg}
            </Alert>
          )
            : (
              <Alert variant="danger">
                {props.displayMsg.msg}
              </Alert>
            )
        ) : null
      }

      {
        // page loading mask
        props.pageLoading === true
          && (
          <div className="overlay">
            <br />
            <Spinner
              animation="border"
              role="status"
              size="lg"
              style={{ width: `${10}rem`, height: `${10}rem` }}
              className="mt-5"
            >
              <span className="sr-only">Loading...</span>
            </Spinner>
            <h5>Loading...</h5>
          </div>
          )
      }
    </div>
  );
}

BaseUIComp.propTypes = {
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  pageLoading: PropTypes.bool.isRequired
};

export default BaseUIComp;
