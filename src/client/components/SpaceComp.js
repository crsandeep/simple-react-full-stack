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
  Alert,
  Badge
} from 'react-bootstrap';
import {
  Formik, Field, Form, ErrorMessage
} from 'formik';
import * as Yup from 'yup';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import SingleBedIcon from '@material-ui/icons/SingleBed';
import KingBedIcon from '@material-ui/icons/KingBed';
import LocalHotelIcon from '@material-ui/icons/LocalHotel';
import WcIcon from '@material-ui/icons/Wc';
import FastfoodIcon from '@material-ui/icons/Fastfood';
import KitchenIcon from '@material-ui/icons/Kitchen';
import WeekendIcon from '@material-ui/icons/Weekend';
import HelpOutlineIcon from '@material-ui/icons/HelpOutline';

import * as Constants from '../constants/Space';

const validateFormSchema = Yup.object().shape({
  name: Yup.string()
    .required('Name is required')
    .min(3, 'Name must be at least 3 characters')
    .trim(),
  location: Yup.string()
    .required('Location is required')
    .min(1, 'Please select location')
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
                  color="textSecondary"
                >
                  {`Grids: ${space.gridCount} - Items: ${space.itemCount}`}
                </Typography>
                <br />
                {
                  space.itemTags.map(tag => (
                    <Badge variant="warning">
                      {tag}
                    </Badge>
                  ))
                }
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
              onClick={() => handleDelete(space.spaceId, space.name)}
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
            <ListSubheader>
              {
                {
                  'Bedroom 1': <SingleBedIcon />,
                  'Bedroom 2': <LocalHotelIcon />,
                  'Bedroom 3': <KingBedIcon />,
                  'Living Room': <WeekendIcon />,
                  'Dinning Room': <FastfoodIcon />,
                  Kitechen: <KitchenIcon />,
                  Bathroom: <WcIcon />,
                  Others: <HelpOutlineIcon />
                }[location]
              }
              {' '}
              {location}
            </ListSubheader>
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
      {
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

      <List className="spaceList-pc" subheader={<li />}>
        {dataList}
      </List>

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
                    <Col xs={12} md={12}>
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
                      <label htmlFor="name">Space Name</label>
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
                    <Col xs={12} md={5}>
                      <label htmlFor="location">Space Location</label>
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
                    <Col xs={12} md={7}>
                      <label htmlFor="imgFile">Display Image</label>
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
  displayMsg: PropTypes.oneOfType([PropTypes.object]).isRequired,
  spaceList: PropTypes.arrayOf(PropTypes.object),
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
