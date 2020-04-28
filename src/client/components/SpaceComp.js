import React, { useRef } from 'react';
import PropTypes from 'prop-types';

import {
  ListItemSecondaryAction,
  List,
  ListItem,
  ListItemText,
  ListSubheader,
  IconButton,
  ListItemAvatar,
  Avatar,
  Typography
} from '@material-ui/core/';
// ui
import '../css/Form.css';
import '../css/Split.css';
import '../css/SpaceList.css';

import {
  Button,
  Modal,
  Row,
  Col,
  Spinner,
  Image,
  Badge,
  Alert
} from 'react-bootstrap';
import {
  Formik, Field, Form, ErrorMessage
} from 'formik';
import * as Yup from 'yup';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import * as Constants from '../constants/Space';

const validateFormSchema = Yup.object().shape({
  name: Yup.string()
    .required('Name is required')
    .min(3, 'Name must be at least 3 characters')
    .trim(),
  colorCode: Yup.string()
    .required('Color is required')
    .min(1, 'Please select Color'),
  location: Yup.string()
    .required('Location is required')
    .min(1, 'Please select location'),
  tags: Yup.string()
    .nullable()
    .min(3, 'Tags must be at least 3 characters')
    .trim(),
  sizeUnit: Yup.string()
    .nullable()
    .when(['sizeWidth', 'sizeHeight', 'sizeDepth'], {
      is: (sizeWidth, sizeHeight, sizeDepth) => sizeWidth > 0 || sizeHeight > 0 || sizeDepth > 0,
      then: Yup.string().required('Unit is required')
    }),
  sizeWidth: Yup.number().nullable().min(0, 'Please enter valid Width'),
  sizeHeight: Yup.number().nullable().min(0, 'Please enter valid Height'),
  sizeDepth: Yup.number().nullable().min(0, 'Please enter valid Depth')
});


function SpaceComp(props) {
  const formRef = useRef();
  const handleSubmit = () => {
    if (formRef.current) {
      formRef.current.handleSubmit();
    }
  };

  // generate left side list bar
  const [selectedSpace, setSelectedSpace] = React.useState();
  const handleSpaceClick = (event, index) => {
    setSelectedSpace(index);
    props.handleSelect(index);
  };

  const getSpaceItem = (spaceList, handleEdit, handleSelect, handleDelete) => {
    const itemList = [];

    for (const space of spaceList) {
      itemList.push(
        <ListItem
          key={space.spaceId}
          alignItems="flex-start"
          button
          selected={selectedSpace === space.spaceId}
          onClick={event => handleSpaceClick(event, space.spaceId)}
        >
          <ListItemAvatar>
            {space.imgPath != null ? (
              <Avatar variant="rounded" alt={space.name} src={space.imgPath} />
            ) : (
              <Avatar variant="rounded" alt={space.name}>
                {
                  space.name.substring(0, 4)
                }
              </Avatar>
            )}
          </ListItemAvatar>
          <ListItemText
            primary={space.name}
            secondary={(
              <React.Fragment>
                <Typography
                  component="span"
                  variant="body2"
                  className="spaceList-inline"
                  color="textPrimary"
                >
                  {space.tags != null
                    && space.tags.length > 0
                    && space.tags.split(',').map(tags => (
                      <span key={`${tags}`}>
                        <Badge variant="warning">
                          #
                          {tags}
                        </Badge>
                        {' '}
                      </span>
                    ))}
                </Typography>
                <br />
                <span>
                  Size (WxHxD):
                  {space.sizeWidth != null ? space.sizeWidth : 'NA'}
                  {' '}
                  x
                  {space.sizeHeight != null ? space.sizeHeight : 'NA'}
                  {' '}
                  x
                  {space.sizeDepth != null ? space.sizeDepth : 'NA'}
                  {space.sizeUnit != null ? ` ${space.sizeUnit}` : ''}
                </span>
              </React.Fragment>
            )}
          />
          <ListItemSecondaryAction>
            <IconButton
              aria-label="edit"
              onClick={() => handleEdit(space.spaceId)}
            >
              <EditIcon />
            </IconButton>
            <IconButton
              aria-label="delete"
              onClick={() => handleDelete(space.spaceId)}
            >
              <DeleteIcon />
            </IconButton>
          </ListItemSecondaryAction>
        </ListItem>
      );
    }
    return itemList;
  };

  const genSpaceList = (spaceList, handleEdit, handleSelect, handleDelete) => {
    const displayList = [];
    const spaceMap = new Map();
    let tempList = null;

    // prepare Map<Location,List<Space>> for further generation
    for (const space of spaceList) {
      // get corresponding list
      if (spaceMap.get(space.location) != null) {
        tempList = spaceMap.get(space.location);
      } else {
        tempList = [];
      }

      // // add to list
      tempList.push(space);

      // update map with latest list
      spaceMap.set(space.location, tempList);
    }

    // generate header and related spaces under each location according to Map settings
    for (const [location, list] of spaceMap) {
      displayList.push(
        <li key={`section-${location}`}>
          <ul className="spaceList-ul">
            <ListSubheader>{location}</ListSubheader>
            {getSpaceItem(list, handleEdit, handleSelect, handleDelete)}
          </ul>
        </li>
      );
    }
    return displayList;
  };

  // list mode
  let dataList = [];
  if (props.spaceList != null && props.spaceList.length > 0) {
    dataList = genSpaceList(
      props.spaceList,
      props.handleEdit,
      props.handleSelect,
      props.handleDelete
    );
  }

  return (
    <div>
      <div>
        {

          props.editStatus !== null ? (
            props.editStatus.isSuccess !== null ? (
              props.editStatus.isSuccess === true ? (
                <Alert variant="success">
                  {props.editStatus.operation}
                  {' '}
                  Successefully
                </Alert>
              ) : (
                <Alert variant="danger">
                  Failed to
                  {props.editStatus.operation}
                  . Error:
                  {props.editStatus.message}
                </Alert>
              )
            ) : null
          ) : null
        }
      </div>

      <List className="spaceList-pc" subheader={<li />}>
        {dataList}
      </List>
      {
        // new space button
        props.formState.formMode === Constants.FORM_READONLY_MODE && (
          <Button variant="primary" onClick={props.handleNew}>
            New Space
          </Button>
        )
      }

      <Button variant="primary" onClick={props.handleReloadList}>
        Refresh
      </Button>


      {
        // page loading mask
        props.formState.pageLoading === true && (
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

      <div>
        <Modal
          show={props.formState.formMode === Constants.FORM_EDIT_MODE}
          onHide={props.handleCancel}
          dialogClassName="modal-90w"
        >
          <Modal.Header closeButton>
            <Modal.Title>Space Details</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Formik
              enableReinitialize
              initialValues={props.formState}
              validationSchema={validateFormSchema}
              onSubmit={props.handleFormSave}
              innerRef={formRef}
            >
              {({ errors, touched }) => (
                <Form>
                  <Row className="justify-content-md-center">
                    <Col xs={12} md={8}>
                      <Field name="imgPath">
                        {({ field, form }) => field.value != null && (
                        <div>
                          <Image src={field.value} fluid />
                          {form.values.imgPath != null && (
                          <IconButton
                            aria-label="delete"
                            className="align-bottom"
                            onClick={() => props.handleRemoveSpaceImg(
                              form.values.spaceId
                            )
                                  }
                          >
                            <DeleteIcon />
                          </IconButton>
                          )}
                        </div>
                        )
                        }
                      </Field>
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={12}>
                      <label htmlFor="name">Name</label>
                      <Field
                        id="name"
                        name="name"
                        type="text"
                        placeholder="Name"
                        className={`form-control${
                          errors.name && touched.name ? ' is-invalid' : ''
                        }`}
                      />
                      <ErrorMessage
                        name="name"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={3}>
                      <label htmlFor="location">Location</label>
                      <Field
                        name="location"
                        as="select"
                        placeholder="Location"
                        className={`form-control${
                          errors.location && touched.location
                            ? ' is-invalid'
                            : ''
                        }`}
                      >
                        <option value="">Please select...</option>
                        <option value="Living Room">Living Room</option>
                        <option value="Dinning Room">Dinning Room</option>
                        <option value="Kitechen">Kitechen</option>
                        <option value="Bathroom">Bathroom</option>
                        <option value="Bedroom 1">Bedroom 1</option>
                        <option value="Bedroom 2">Bedroom 2</option>
                        <option value="Bedroom 3">Bedroom 3</option>
                        <option value="Others">Others</option>
                      </Field>
                      <ErrorMessage
                        name="location"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                    <Col xs={12} md={3}>
                      <label htmlFor="colorCode">Color Code</label>
                      <Field
                        name="colorCode"
                        as="select"
                        placeholder="Color"
                        className={`form-control${
                          errors.colorCode && touched.colorCode
                            ? ' is-invalid'
                            : ''
                        }`}
                      >
                        <option value="">Please select...</option>
                        <option value="Light">Light</option>
                        <option value="Primary">Blue</option>
                        <option value="Secondary">Grey</option>
                        <option value="Success">Green</option>
                        <option value="Danger">Red</option>
                        <option value="Warning">Yellow</option>
                        <option value="Info">Cyan</option>
                      </Field>
                      <ErrorMessage
                        name="colorCode"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                    <Col xs={12} md={3}>
                      <label htmlFor="tags">Tags</label>
                      <Field
                        name="tags"
                        type="text"
                        placeholder="Use commas to separate Tags"
                        className={`form-control${
                          errors.tags && touched.tags ? ' is-invalid' : ''
                        }`}
                      />
                      <ErrorMessage
                        name="tags"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                    <Col xs={12} md={3}>
                      <label htmlFor="imgFile">Image</label>
                      <Field name="imgFile">
                        {({ form }) => (
                          <input
                            type="file"
                            onChange={event => form.setFieldValue(
                              'imgFile',
                              event.target.files[0]
                            )
                            }
                            accept="image/*"
                            className={`form-control${
                              errors.imgFile && touched.imgFile
                                ? ' is-invalid'
                                : ''
                            }`}
                          />
                        )}
                      </Field>
                      <ErrorMessage
                        name="imgFile"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                  </Row>
                  <Row>
                    <Col xs={12} md={2}>
                      <label htmlFor="sizeWidth">Width</label>
                      <Field name="sizeWidth">
                        {({ field }) => (
                          <input
                            type="number"
                            {...field}
                            placeholder="Width"
                            className={`form-control${
                              errors.sizeWidth && touched.sizeWidth
                                ? ' is-invalid'
                                : ''
                            }`}
                          />
                        )}
                      </Field>
                      <ErrorMessage
                        name="sizeWidth"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                    <Col xs={12} md={2}>
                      <label htmlFor="sizeHeight">Height</label>
                      <Field name="sizeHeight">
                        {({ field }) => (
                          <input
                            type="number"
                            {...field}
                            placeholder="Height"
                            className={`form-control${
                              errors.sizeHeight && touched.sizeHeight
                                ? ' is-invalid'
                                : ''
                            }`}
                          />
                        )}
                      </Field>
                      <ErrorMessage
                        name="sizeHeight"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                    <Col xs={12} md={2}>
                      <label htmlFor="sizeDepth">Depth</label>
                      <Field name="sizeDepth">
                        {({ field }) => (
                          <input
                            type="number"
                            {...field}
                            placeholder="Depth"
                            className={`form-control${
                              errors.sizeDepth && touched.sizeDepth
                                ? ' is-invalid'
                                : ''
                            }`}
                          />
                        )}
                      </Field>
                      <ErrorMessage
                        name="sizeDepth"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                    <Col xs={12} md={2}>
                      <label htmlFor="sizeUnit">Unit</label>
                      <Field
                        name="sizeUnit"
                        as="select"
                        placeholder="Unit"
                        className={`form-control${
                          errors.sizeUnit && touched.sizeUnit
                            ? ' is-invalid'
                            : ''
                        }`}
                      >
                        <option value="">Please select...</option>
                        <option value="cm">cm</option>
                        <option value="m">m</option>
                        <option value="inch">inch</option>
                        <option value="feet">feet</option>
                      </Field>
                      <ErrorMessage
                        name="sizeUnit"
                        component="div"
                        className="invalid-feedback"
                      />
                    </Col>
                  </Row>
                </Form>
              )}
            </Formik>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={props.handleCancel}>
              Close
            </Button>
            <Button id="btnSave" variant="primary" onClick={handleSubmit}>
              Save changes
            </Button>
          </Modal.Footer>
        </Modal>
      </div>
    </div>
  );
}
SpaceComp.defaultProps = {
  spaceList: []
};

SpaceComp.propTypes = {
  spaceList: PropTypes.arrayOf(PropTypes.object),
  editStatus: PropTypes.oneOfType([PropTypes.object]).isRequired,
  formState: PropTypes.oneOfType([PropTypes.object]).isRequired,
  handleFormSave: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
  handleNew: PropTypes.func.isRequired,
  handleEdit: PropTypes.func.isRequired,
  handleDelete: PropTypes.func.isRequired,
  handleReloadList: PropTypes.func.isRequired,
  handleRemoveSpaceImg: PropTypes.func.isRequired,
  handleSelect: PropTypes.func.isRequired
};

export default SpaceComp;
