import React from 'react';
// eslint-disable-next-line import/no-duplicates
import { useRef } from 'react';
import PropTypes from 'prop-types';

// ui
import '../css/Form.css';

import Button from '@material-ui/core/Button';
import Link from '@material-ui/core/Link';
import Typography from '@material-ui/core/Typography';
import Box from '@material-ui/core/Box';

import Modal from 'react-bootstrap/Modal';
import Tabs from 'react-bootstrap/Tabs';
import Tab from 'react-bootstrap/Tab';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faSignInAlt, faUser
} from '@fortawesome/free-solid-svg-icons';

import {
  Formik, Field, Form, ErrorMessage
} from 'formik';
import * as Yup from 'yup';
import BaseUIComp from './BaseUIComp';

const loginSchema = Yup.object().shape({
  email: Yup.string().email()
    .required('Email is required')
    .trim(),
  password: Yup.string()
    .required('Password is required')
    .min(6, 'At least 6 characters')
    .trim()
});


const regSchema = Yup.object().shape({
  name: Yup.string()
    .required('Name is required')
    .trim(),
  email: Yup.string().email()
    .required('Email is required')
    .trim(),
  password: Yup.string()
    .required('Password is required')
    .min(6, 'At least 6 characters')
    .trim()
  // verifyPassword: Yup.string()
  //   .required('Confirm password is required')
  //   .when('password', {
  //     is: val => (!!(val && val.length > 0)),
  //     then: Yup.string().oneOf(
  //       [Yup.ref('password')],
  //       'Password not match'
  //     )
  //   })
});


function AuthComp(props) {
  const formRef = useRef();
  const regFormRef = useRef();

  const handleSubmit = () => {
    if (formRef.current) {
      formRef.current.handleSubmit();
    }
  };

  const handleRegSubmit = () => {
    if (regFormRef.current) {
      regFormRef.current.handleSubmit();
    }
  };

  return (
    <div>
      <BaseUIComp
        pageLoading={props.pageLoading}
      />

      <Modal
        show={props.isShow}
        onHide={props.handleClose}
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>Welcome to Space Master</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Tabs defaultActiveKey="login" id="uncontrolled-tab-example">
            <Tab
              eventKey="login"
              title={(
                <span>
                  <FontAwesomeIcon icon={faSignInAlt} style={{ fontSize: '1.75em', verticalAlign: 'middle' }} />
                  {' '}
                  Login
                </span>
              )}
            >
              <Box>
                <Formik
                  initialValues={{
                    // password: '',
                    // email: ''

                    email: '6@test.com',
                    password: '123467'
                  }}
                  validationSchema={loginSchema}
                  onSubmit={props.handleLogin}
                  innerRef={formRef}
                >
                  {({ values, errors, touched }) => (
                    <Form>
                      <div>
                        <label htmlFor="email" className="required-field">Email</label>
                        <Field name="email" type="text" placeholder="Enter Email" className={`form-control${errors.email && touched.email ? ' is-invalid' : ''}`} />
                        <ErrorMessage name="email" component="div" className="invalid-feedback" />
                      </div>
                      <div>
                        <label htmlFor="password" className="required-field">Password</label>
                        <Field name="password" type="password" placeholder="Enter Password" className={`form-control${errors.password && touched.password ? ' is-invalid' : ''}`} />
                        <ErrorMessage name="password" component="div" className="invalid-feedback" />
                      </div>

                      <br />
                      <Button onClick={handleSubmit} variant="contained" color="primary" fullWidth>
                        Login
                      </Button>

                      {
                        props.displayMsg.isLoginMode != null
                        && props.displayMsg.isLoginMode === true ? (
                          <div>
                            <br />
                            <Typography variant="body2" align="center" display="block" gutterBottom color="error">
                              {props.displayMsg.msg}
                            </Typography>
                          </div>
                          ) : (
                            null
                          )
                      }

                      <Typography variant="caption" align="right" display="block" gutterBottom>
                        <Link href="#" onClick={handleSubmit} underline="always">
                          Forgot Password?
                        </Link>
                      </Typography>
                    </Form>
                  )}
                </Formik>
              </Box>
            </Tab>
            <Tab
              eventKey="register"
              title={(
                <span>
                  <FontAwesomeIcon icon={faUser} style={{ fontSize: '1.75em', verticalAlign: 'middle' }} />
                  {' '}
                  Register
                </span>
            )}
            >
              <Box>
                <Formik
                  enableReinitialize
                      // initialValues={props.formState}
                  initialValues={{
                    name: 't111',
                    email: '1@test.com',
                    password: '123467',
                    verifyPassword: '123467'
                  }}
                  validationSchema={regSchema}
                  onSubmit={props.handleRegister}
                  innerRef={regFormRef}
                >
                  {({ values, errors, touched }) => (
                    <Form>
                      <div>
                        <label htmlFor="name" className="required-field">Name</label>
                        <Field name="name" type="text" placeholder="Enter Name" className={`form-control${errors.name && touched.name ? ' is-invalid' : ''}`} />
                        <ErrorMessage name="name" component="div" className="invalid-feedback" />
                      </div>
                      <div>
                        <label htmlFor="email" className="required-field">Email</label>
                        <Field name="email" type="text" placeholder="Enter Email" className={`form-control${errors.email && touched.email ? ' is-invalid' : ''}`} />
                        <ErrorMessage name="email" component="div" className="invalid-feedback" />
                      </div>
                      <div>
                        <label htmlFor="password" className="required-field">Password</label>
                        <Field name="password" type="password" placeholder="Enter Password" className={`form-control${errors.password && touched.password ? ' is-invalid' : ''}`} />
                        <ErrorMessage name="password" component="div" className="invalid-feedback" />
                      </div>
                      <div>
                        <label htmlFor="verifyPassword" className="required-field">Confirm Password</label>
                        <Field name="verifyPassword" type="password" placeholder="Enter Password Again" className={`form-control${errors.verifyPassword && touched.verifyPassword ? ' is-invalid' : ''}`} />
                        <ErrorMessage name="verifyPassword" component="div" className="invalid-feedback" />
                      </div>

                      <br />
                      <Button onClick={handleRegSubmit} variant="contained" color="primary" fullWidth>
                        Register
                      </Button>

                      {
                        props.displayMsg.isLoginMode != null
                        && props.displayMsg.isLoginMode === false ? (
                          <div>
                            <br />
                            <Typography variant="body2" align="center" display="block" gutterBottom color="error">
                              {props.displayMsg.msg}
                            </Typography>
                          </div>
                          ) : (
                            null
                          )
                      }

                    </Form>
                  )}
                </Formik>
              </Box>
            </Tab>
          </Tabs>
        </Modal.Body>
      </Modal>
    </div>
  );
}
AuthComp.propTypes = {
  isShow: PropTypes.bool.isRequired,
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  pageLoading: PropTypes.bool.isRequired,
  handleClose: PropTypes.func.isRequired,
  handleLogin: PropTypes.func.isRequired,
  handleRegister: PropTypes.func.isRequired
};

export default AuthComp;
