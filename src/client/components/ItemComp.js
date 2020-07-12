import React from 'react';
// eslint-disable-next-line import/no-duplicates
import { useRef } from 'react';
import PropTypes from 'prop-types';

// ui
import '../css/Form.css';
import 'react-datepicker/dist/react-datepicker.css';

import {
  Cached, Add, ArrowBackIos, AddAlert, Delete
} from '@material-ui/icons';

import {
  IconButton, Box, Divider, FormControlLabel, Switch
} from '@material-ui/core/';
import {
  Button, Modal, Row, Col, Image
} from 'react-bootstrap';
import {
  Formik, Field, Form, ErrorMessage
} from 'formik';


import * as Yup from 'yup';
import DatePicker from 'react-datepicker';
import * as Constants from '../constants/Item';
import ItemListComp from './ItemListComp';
import ItemCardComp from './ItemCardComp';
import BaseUIComp from './BaseUIComp';
import Configs from '../config';

const validateFormSchema = Yup.object().shape({
  name: Yup.string()
    .required('Name is required')
    .min(3, 'Name must be at least 3 characters')
    .trim(),
  colorCode: Yup.string()
    .required('Color is required')
    .min(1, 'Please select Card Color'),
  description: Yup.string().nullable()
    .min(3, 'Description must be at least 3 characters')
    .trim(),
  tags: Yup.string().nullable()
    .min(3, '#Tags must be at least 3 characters')
    .trim(),
  category: Yup.string()
    .required('Category is required')
    .min(1, 'Please select Category')
});

function ItemComp(props) {
  const formRef = useRef();
  const handleSubmit = () => {
    if (formRef.current) {
      formRef.current.handleSubmit();
    }
  };


  // hook for switch view
  const [state, setState] = React.useState({
    isListView: false
  });
  const handleChange = (event) => {
    setState({ ...state, [event.target.name]: event.target.checked });
  };


  return (
    <div>
      <BaseUIComp
        displayMsg={props.displayMsg}
        pageLoading={props.pageLoading}
      />

      <Row>
        <Col xs={2} md={2}>
          <Box display="flex" justifyContent="flex-start">
            <IconButton
              aria-label="back"
              onClick={() => props.handleGoBack()}
              size="small"
            >
              <ArrowBackIos />
            </IconButton>
          </Box>
        </Col>
        <Col xs={10} md={10}>
          <Box display="flex" justifyContent="flex-end">
            <IconButton aria-label="New" onClick={props.handleNew} size="small">
              <Add />
            </IconButton>
            <IconButton aria-label="Reload" onClick={props.handleReloadList} size="small">
              <Cached />
            </IconButton>
            <FormControlLabel
              control={(
                <Switch
                  checked={state.isListView}
                  onChange={handleChange}
                  name="isListView"
                  color="primary"
                  size="small"
                />
                )}
              label="List"
              style={{ marginTop: '10px', marginLeft: '5px' }}
            />
          </Box>
        </Col>
      </Row>
      <Divider />
      <Row>
        <Col xs={12} md={12}>

          {
            !state.isListView ? (
              <ItemCardComp
                isShowLocation={false}
                isReadOnly={false}
                itemList={props.itemList}
                handleEdit={props.handleEdit}
              />
            ) : (
              <ItemListComp
                isShowLocation={false}
                isReadOnly={false}
                itemList={props.itemList}
                handleEdit={props.handleEdit}
              />
            )
          }
        </Col>
      </Row>

      <div>
        <Modal
          show={props.formState.formMode === Constants.FORM_EDIT_MODE}
          onHide={props.handleCancel}
          centered
        >
          <Modal.Header closeButton>
            <Modal.Title>Details</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Formik
              enableReinitialize
              initialValues={props.formState}
              validationSchema={validateFormSchema}
              onSubmit={props.handleFormSave}
              innerRef={formRef}
            >
              {({ values, errors, touched }) => (
                <Form>
                  <Row className="justify-content-md-center">
                    <Col xs={12} md={8}>
                      <Field name="imgPath">
                        {({ field, form, meta }) => (
                          field.value != null
                            && (
                            <div>
                              <Image

                                src={`${Configs.BACKEND_SERVER_URL}/${field.value}`}
                                className="modal-lg-image"
                                fluid
                              />
                              {
                                form.values.imgPath != null
                                && (
                                <IconButton
                                  aria-label="delete"
                                  className="align-bottom"
                                  onClick={() => props.handleRemoveItemImg(form.values.itemId)}
                                  size="small"
                                >
                                  <Delete />
                                </IconButton>
                                )
                              }
                            </div>
                            )
                        )}
                      </Field>
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={12}>
                      <label htmlFor="name" className="required-field">Name</label>
                      <Field name="name" type="text" placeholder="Your Item Name" className={`form-control${errors.name && touched.name ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="name" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={7} md={6}>
                      <label htmlFor="category" className="required-field">Category</label>
                      <Field name="category" as="select" placeholder="Category" className={`form-control${errors.category && touched.category ? ' is-invalid' : ''}`}>
                        <option value="">Please select...</option>
                        <option value="Favorite">Favorite</option>
                        <option value="Gifts">Gifts</option>
                        <option value="Clothes">Clothes</option>
                        <option value="Shoes">Shoes</option>
                        <option value="Collections">Collections</option>
                        <option value="Baby">Baby</option>
                        <option value="Books">Books</option>
                        <option value="Travel">Travel</option>
                        <option value="Food">Food</option>
                        <option value="Kitchenware">Kitchenware</option>
                        <option value="Tools">Tools</option>
                        <option value="Others">Others</option>
                      </Field>
                      <ErrorMessage name="category" component="div" className="invalid-feedback" />
                    </Col>
                    <Col xs={5} md={6}>
                      <label htmlFor="colorCode" className="required-field">Color</label>
                      <Field name="colorCode" as="select" placeholder="Color" className={`form-control${errors.colorCode && touched.colorCode ? ' is-invalid' : ''}`}>
                        <option value="">Please select...</option>
                        <option value="Light" default>Light</option>
                        <option value="Primary">Blue</option>
                        {/* <option value="Secondary">Grey</option> */}
                        <option value="Success">Green</option>
                        <option value="Danger">Red</option>
                        <option value="Info">Cyan</option>
                      </Field>
                      <ErrorMessage name="colorCode" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={7} md={6}>
                      <label htmlFor="tags">Custom Labels</label>
                      <Field name="tags" type="text" placeholder="Use commas to separate" className={`form-control${errors.tags && touched.tags ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="tags" component="div" className="invalid-feedback" />
                    </Col>
                    <Col xs={5} md={6}>
                      <label htmlFor="imgFile">Photo</label>
                      <Field name="imgFile">
                        {({ field, form, meta }) => (
                          <input
                            type="file"
                            onChange={event => form.setFieldValue('imgFile', event.target.files[0])
                              }
                            accept="image/*"
                            className={`form-control${errors.imgFile && touched.imgFile ? ' is-invalid' : ''}`}
                          />
                        )}
                      </Field>
                      <ErrorMessage name="imgFile" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={12}>
                      <label htmlFor="description">Description</label>
                      <Field
                        name="description"
                        component="textarea"
                        placeholder="E.g. 2nd Wedding Anniversary gift from your wife. "
                        className={`form-control${errors.description && touched.description ? ' is-invalid' : ''}`}
                      />
                      <ErrorMessage name="description" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={6}>
                      <AddAlert />
                      {/* <label htmlFor="reminderDtm">Reminder</label> */}
                      <Field name="reminderDtm">
                        {({ field, form, meta }) => (
                          <DatePicker
                            onChange={date => form.setFieldValue('reminderDtm', date)
                              }
                            selected={values.reminderDtm}
                            dateFormat="dd-MMM-yyyy hh:mm aa"
                            placeholder="Reminder"
                            todayButton="Today"
                            showTimeSelect
                            timeIntervals={15}
                            className={`datepicker-200w form-control${errors.reminderDtm && touched.reminderDtm ? ' is-invalid' : ''}`}
                          />
                        )}
                      </Field>
                      {/* <ErrorMessage name="reminderDtm" component="div" className="invalid-feedback" /> */}
                    </Col>
                  </Row>
                </Form>
              )}
            </Formik>
          </Modal.Body>
          <Modal.Footer>
            <Button
              variant="danger"
              onClick={() => (props.handleDelete(props.formState.itemId, props.formState.name, props.formState.description))}
            >
              Delete
            </Button>
            <Button variant="primary" onClick={handleSubmit}>Save</Button>
          </Modal.Footer>
        </Modal>
      </div>
    </div>
  );
}

ItemComp.defaultProps = {
  itemList: []
};

ItemComp.propTypes = {
  itemList: PropTypes.arrayOf(PropTypes.object),
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  pageLoading: PropTypes.bool.isRequired,
  handleFormSave: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  handleNew: PropTypes.func.isRequired,
  handleEdit: PropTypes.func.isRequired,
  handleDelete: PropTypes.func.isRequired,
  handleReloadList: PropTypes.func.isRequired,
  handleRemoveItemImg: PropTypes.func.isRequired,
  handleGoBack: PropTypes.func.isRequired
};

export default ItemComp;
