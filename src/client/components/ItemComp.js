import React from 'react';
// eslint-disable-next-line import/no-duplicates
import { useRef } from 'react';
import PropTypes from 'prop-types';

// ui
import '../css/Form.css';
import 'react-datepicker/dist/react-datepicker.css';
import {
  IconButton
} from '@material-ui/core/';
import {
  Button, Modal, Row, Col, ButtonToolbar, Image
} from 'react-bootstrap';
import {
  Formik, Field, Form, ErrorMessage
} from 'formik';
import * as Yup from 'yup';
import DatePicker from 'react-datepicker';
import AddAlertIcon from '@material-ui/icons/AddAlert';
import DeleteIcon from '@material-ui/icons/Delete';
import ArrowBackIosIcon from '@material-ui/icons/ArrowBackIos';
import AddCircleOutlineIcon from '@material-ui/icons/AddCircleOutline';
import RefreshIcon from '@material-ui/icons/Refresh';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';
import * as Constants from '../constants/Item';
import ItemListComp from './ItemListComp';
import ItemCardComp from './ItemCardComp';
import BaseUIComp from './BaseUIComp';

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
        pageLoading={props.formState.pageLoading}
      />

      <Row>
        <Col xs={2} md={1}>
          <IconButton
            aria-label="back"
            onClick={() => props.handleGoBack()}
          >
            <ArrowBackIosIcon />
          </IconButton>
        </Col>
        <Col xs={10} md={11}>
          <ButtonToolbar>
            {
                // new item button
                props.formState.formMode === Constants.FORM_READONLY_MODE
                  && (
                  <IconButton aria-label="New" onClick={props.handleNew}>
                    <AddCircleOutlineIcon />
                  </IconButton>
                  )
              }

            <IconButton aria-label="Cancel" onClick={props.handleReloadList}>
              <RefreshIcon />
            </IconButton>

            <FormControlLabel
              control={(
                <Switch
                  checked={state.isListView}
                  onChange={handleChange}
                  name="isListView"
                  color="primary"
                />
              )}
              label="List View"
            />
          </ButtonToolbar>
        </Col>
      </Row>
      <Row>
        <Col xs={12} md={12}>

          {
            !state.isListView ? (
              <ItemCardComp
                isShowLocation={false}
                itemList={props.itemList}
                handleEdit={props.handleEdit}
                handleDelete={props.handleDelete}
              />
            ) : (
              <ItemListComp
                isShowLocation={false}
                itemList={props.itemList}
                handleEdit={props.handleEdit}
                handleDelete={props.handleDelete}
              />
            )
          }
        </Col>
      </Row>

      <div>
        <Modal
          show={props.formState.formMode === Constants.FORM_EDIT_MODE}
          onHide={props.handleCancel}
        >
          <Modal.Header closeButton>
            <Modal.Title>Item Details</Modal.Title>
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
                              <Image src={field.value} fluid />
                              {
                                form.values.imgPath != null
                                && (
                                <IconButton
                                  aria-label="delete"
                                  className="align-bottom"
                                  onClick={() => props.handleRemoveItemImg(form.values.itemId)
                                  }
                                >
                                  <DeleteIcon />
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
                    <Col xs={12} md={6}>
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
                    <Col xs={12} md={6}>
                      <label htmlFor="tags">#Tags</label>
                      <Field name="tags" type="text" placeholder="Use commas to separate" className={`form-control${errors.tags && touched.tags ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="tags" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={6}>
                      <label htmlFor="colorCode" className="required-field">Card Color</label>
                      <Field name="colorCode" as="select" placeholder="Color" className={`form-control${errors.colorCode && touched.colorCode ? ' is-invalid' : ''}`}>
                        <option value="">Please select...</option>
                        <option value="Light" default>Light</option>
                        <option value="Primary">Blue</option>
                        <option value="Secondary">Grey</option>
                        <option value="Success">Green</option>
                        <option value="Danger">Red</option>
                        <option value="Info">Cyan</option>
                      </Field>
                      <ErrorMessage name="colorCode" component="div" className="invalid-feedback" />
                    </Col>
                    <Col xs={12} md={6}>
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
                      <label htmlFor="reminderDtm">Reminder</label>
                      <AddAlertIcon />
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
                      <ErrorMessage name="reminderDtm" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                </Form>
              )}
            </Formik>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={props.handleCancel}>Close</Button>
            <Button id="btnSave" variant="primary" onClick={handleSubmit}>Save changes</Button>
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
