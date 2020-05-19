import React from 'react';
// eslint-disable-next-line import/no-duplicates
import { useRef } from 'react';

import PropTypes from 'prop-types';
// import RemindNoteComp from './common/RemindNoteComp';

// ui
import '../css/Form.css';
import 'react-datepicker/dist/react-datepicker.css';

import {
  Button, Modal, Row, Col, Card, ButtonToolbar, CardColumns,
  Spinner, Image, Badge, Alert, Breadcrumb
} from 'react-bootstrap';
import {
  Formik, Field, Form, ErrorMessage
} from 'formik';
import * as Yup from 'yup';
import DatePicker from 'react-datepicker';
import AddAlertIcon from '@material-ui/icons/AddAlert';
import { IconButton } from '@material-ui/core';
import LabelIcon from '@material-ui/icons/Label';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import CardGiftcardIcon from '@material-ui/icons/CardGiftcard';
import ArrowBackIosIcon from '@material-ui/icons/ArrowBackIos';

import Breadcrumbs from '@material-ui/core/Breadcrumbs';
import Link from '@material-ui/core/Link';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import * as Constants from '../constants/Item';

const validateFormSchema = Yup.object().shape({
  name: Yup.string()
    .required('Name is required')
    .min(3, 'Name must be at least 3 characters')
    .trim(),
  colorCode: Yup.string()
    .required('Color is required')
    .min(1, 'Please select Color'),
  description: Yup.string().nullable()
    .min(3, 'Description must be at least 3 characters')
    .trim(),
  tags: Yup.string().nullable()
    .min(3, 'Tags must be at least 3 characters')
    .trim(),
  category: Yup.string()
    .required('Category is required')
    .min(1, 'Please select Category')
});

// generate item list content
const genItemData = (item, key, handleEdit, handleDelete) => {
  let tagsArr = {};
  if (item.tags != null && item.tags.length > 0) {
    tagsArr = item.tags.split(',');
  }

  return (
    <Card key={key} bg={item.colorCode.toLowerCase()}>
      {
        item.imgPath != null
          && <Card.Img variant="top" src={item.imgPath} />
    }
      <Card.Header>
        <CardGiftcardIcon />
        {' '}
        {' '}
        {item.name}
        <Badge className="float-right" variant="light">
          <LabelIcon />
          {item.category}
        </Badge>
      </Card.Header>
      <Card.Body>
        <Card.Text>
          {item.description}
        </Card.Text>
        <div>
          <Row>
            <Col xs={12} md={7}>
              {
              tagsArr != null && tagsArr.length > 0
              && tagsArr.map((tags, i) => (
                <span key={i}>
                  <Badge variant="warning">
                    #
                    {tags}
                  </Badge>
                  {' '}
                </span>
              ))
            }
            </Col>
            <Col xs={12} md={5}>
              <ButtonToolbar>
                <IconButton aria-label="edit" onClick={() => handleEdit(item.itemId)}>
                  <EditIcon />
                </IconButton>
                <IconButton aria-label="delete" onClick={() => handleDelete(item.itemId)}>
                  <DeleteIcon />
                </IconButton>
              </ButtonToolbar>
            </Col>
          </Row>
        </div>
      </Card.Body>
      <Card.Footer>
        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
          <Link color="inherit" href="/space">
            <i className="fa fa-fw fa-home" style={{ fontSize: '1.05em' }} />
            {
              // show space name
              `${item.spaceLocation} - ${item.spaceName}`
            }
          </Link>
          <Link color="inherit" href="/grid">
            <i className="fa fa-fw fa-table" style={{ fontSize: '1.05em' }} />
            {
              // show location with grid ID with 2 digits
              item.gridId.toString().padStart(2, '0').slice(-3)
            }
          </Link>
        </Breadcrumbs>
        {
          item.reminderDtm != null
            && (
            <div>
              {item.reminderDtm}
            </div>
            )
        // <RemindNoteComp remindDtm={item.reminderDtm}></RemindNoteComp>
        }
      </Card.Footer>
    </Card>
  );
};

function ItemComp(props) {
  const formRef = useRef();
  const handleSubmit = () => {
    if (formRef.current) {
      formRef.current.handleSubmit();
    }
  };

  // generate item data
  const displayList = [];
  if (props.itemList != null) {
    for (let i = 0; i <= props.itemList.length - 1; i++) {
      displayList.push(genItemData(props.itemList[i], i, props.handleEdit, props.handleDelete));
    }
  }

  return (
    <div>
      <div>
        {
          // props.editStatus!==null ? (
          //   props.editStatus.isSuccess !== null ? (
          //     props.editStatus.isSuccess === true ? (
          //       <Alert variant='success'>
          //         {props.editStatus.operation} Successefully
          //       </Alert>

          //     ) :
          //       <Alert variant='danger'>
          //           Failed to {props.editStatus.operation}. Error: {props.editStatus.message}
          //         </Alert>
          //   ):null
          // ):null
        }
      </div>

      {
        // page loading mask
        props.formState.pageLoading === true
          && (
          <div className="overlay">
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

      <IconButton
        aria-label="delete"
        onClick={() => props.handleGoBack()}
      >
        <ArrowBackIosIcon />
      </IconButton>
      {
        // new item button
        props.formState.formMode === Constants.FORM_READONLY_MODE
          && <Button variant="primary" onClick={props.handleNew}>New Item</Button>
      }

      <Button variant="primary" onClick={props.handleReloadList}>Refresh</Button>

      <CardColumns>
        {displayList}
      </CardColumns>

      <div>
        <Modal
          show={props.formState.formMode === Constants.FORM_EDIT_MODE}
          onHide={props.handleCancel}
          dialogClassName="modal-90w"
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
                      <label htmlFor="name">Name</label>
                      <Field name="name" type="text" placeholder="Name" className={`form-control${errors.name && touched.name ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="name" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={3}>
                      <label htmlFor="colorCode">Color</label>
                      <Field name="colorCode" as="select" placeholder="Color" className={`form-control${errors.colorCode && touched.colorCode ? ' is-invalid' : ''}`}>
                        <option value="">Please select...</option>
                        <option value="Light">Light</option>
                        <option value="Primary">Blue</option>
                        <option value="Secondary">Grey</option>
                        <option value="Success">Green</option>
                        <option value="Danger">Red</option>
                        <option value="Warning">Yellow</option>
                        <option value="Info">Cyan</option>
                      </Field>
                      <ErrorMessage name="colorCode" component="div" className="invalid-feedback" />
                    </Col>
                    <Col xs={12} md={3}>
                      <label htmlFor="tags">Tags</label>
                      <Field name="tags" type="text" placeholder="Use commas to separate Tags" className={`form-control${errors.tags && touched.tags ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="tags" component="div" className="invalid-feedback" />
                    </Col>
                    <Col xs={12} md={3}>
                      <label htmlFor="category">Category</label>
                      <Field name="category" as="select" placeholder="Category" className={`form-control${errors.category && touched.category ? ' is-invalid' : ''}`}>
                        <option value="">Please select...</option>
                        <option value="Clothes">Clothes</option>
                        <option value="Shoes">Shoes</option>
                        <option value="Collections">Collections</option>
                        <option value="Books">Books</option>
                        <option value="Kitchenware">Kitchenware</option>
                        <option value="Tools">Tools</option>
                        <option value="Others">Others</option>
                      </Field>
                      <ErrorMessage name="category" component="div" className="invalid-feedback" />
                    </Col>
                    <Col xs={12} md={3}>
                      <label htmlFor="imgFile">Image</label>
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
                      <Field name="description" component="textarea" placeholder="Description" className={`form-control${errors.description && touched.description ? ' is-invalid' : ''}`} />
                      <ErrorMessage name="description" component="div" className="invalid-feedback" />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={3}>
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
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
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
