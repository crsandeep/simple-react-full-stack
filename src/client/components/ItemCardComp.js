import React from 'react';
import PropTypes from 'prop-types';

// ui
import '../css/Form.css';
import 'react-datepicker/dist/react-datepicker.css';
import {
  IconButton
} from '@material-ui/core/';
import {
  Row, Col, Card, CardColumns, Badge
} from 'react-bootstrap';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import CardGiftcardIcon from '@material-ui/icons/CardGiftcard';
import MenuBookIcon from '@material-ui/icons/MenuBook';
import BuildIcon from '@material-ui/icons/Build';
import EmojiEventsIcon from '@material-ui/icons/EmojiEvents';
import FavoriteBorderIcon from '@material-ui/icons/FavoriteBorder';
import FlightIcon from '@material-ui/icons/Flight';
import RestaurantIcon from '@material-ui/icons/Restaurant';
import KitchenIcon from '@material-ui/icons/Kitchen';
import HelpOutlineIcon from '@material-ui/icons/HelpOutline';
import ChildFriendlyIcon from '@material-ui/icons/ChildFriendly';
import Breadcrumbs from '@material-ui/core/Breadcrumbs';
import Link from '@material-ui/core/Link';
import NavigateNextIcon from '@material-ui/icons/NavigateNext';
import RemindNoteComp from './RemindNoteComp';

// generate item content in card view
const genCardData = (itemList, handleEdit, handleDelete) => {
  if (itemList == null) return;
  const displayList = [];

  for (const item of itemList) {
    let tagsArr = [];
    if (item.tags != null && item.tags.length > 0) {
      tagsArr = item.tags.split(',');
    }

    displayList.push(
      <Card key={item.itemId} bg={item.colorCode.toLowerCase()}>
        {
          item.imgPath != null
            && <Card.Img variant="top" src={item.imgPath} />
        }
        <Card.Header>
          {item.name}
          <Badge className="float-right" variant="light">
            {
              {
                Favorite: <FavoriteBorderIcon />,
                Travel: <FlightIcon />,
                Clothes: <i className="fas fa-tshirt" />,
                Shoes: <i className="fas fa-shoe-prints" />,
                Collections: <EmojiEventsIcon />,
                Baby: <ChildFriendlyIcon />,
                Books: <MenuBookIcon />,
                Gifts: <CardGiftcardIcon />,
                Food: <RestaurantIcon />,
                Kitchenware: <KitchenIcon />,
                Tools: <BuildIcon />,
                Others: <HelpOutlineIcon />
              }[item.category]
            }
            {' '}
            {' '}
            {item.category}
          </Badge>
        </Card.Header>

        {/* //card content, description + tags */}
        {
          item.description != null
            || (tagsArr != null && tagsArr.length > 0) ? (
              <Card.Body>
                {/* //description row */}
                {
                  item.description != null ? (
                    <Row>
                      <Col xs={12} md={12}>
                        <Card.Text>{item.description}</Card.Text>
                      </Col>
                    </Row>
                  )
                    : null
                }

                {/* //tags row */}
                {
                  tagsArr != null && tagsArr.length > 0
                  && (
                  <Row>
                    <Col xs={12} md={12}>
                      {
                            tagsArr.map((tags, i) => (
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
                  </Row>
                  )
                }
              </Card.Body>
            ) : null
        }

        <Card.Footer>
          {/* //reminder + button */}
          <Row>
            <Col xs={12} md={12}>
              {/* //Reminder */}
              <div>
                <RemindNoteComp remindDtm={item.reminderDtm} />

                <span style={{ float: 'right' }}>
                  <IconButton aria-label="edit" onClick={() => handleEdit(item.itemId)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton aria-label="delete" onClick={() => handleDelete(item.itemId, item.name, item.description)}>
                    <DeleteIcon />
                  </IconButton>
                </span>
              </div>
            </Col>
          </Row>

          {/* //location path */}
          <Row>
            <Col xs={12} md={12}>
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
            </Col>
          </Row>
        </Card.Footer>
      </Card>
    );
  }
  return displayList;
};

function ItemCardComp(props) {
  // generate item data
  const dataList = genCardData(props.itemList, props.handleEdit, props.handleDelete);

  return (
    <CardColumns>
      {dataList}
    </CardColumns>
  );
}

ItemCardComp.defaultProps = {
  itemList: []
};

ItemCardComp.propTypes = {
  itemList: PropTypes.arrayOf(PropTypes.object),
  handleEdit: PropTypes.func.isRequired,
  handleDelete: PropTypes.func.isRequired
};

export default ItemCardComp;
